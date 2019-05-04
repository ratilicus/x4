#!/usr/bin/env python3.7

"""
Extract xmf files into Wavefront objs (that can be opened in 3D cad software like Blender
Use: python3.7 xmf2obj.py {path/to/filename.xmf}

Extracting should put the object files inside PWD/objs/{model name}/model.obj

python 3.6+ required

XUMF reading logic based on: https://github.com/hhrhhr/Lua-utils-for-X-Rebirth/blob/master/
"""

import gzip
import sys
import logging
import os
import zlib
import glob
from io import BytesIO
from PIL import Image, ImageDraw
from x4lib import get_config, require_python_version, ModUtilMixin
from xmflib import XMFException, XMFHeader, XMFChunk, XMFMaterial, VERTEX, NORMAL, UV

require_python_version(3, 6)
logger = logging.getLogger('x4.' + __name__)


class XMFReader(ModUtilMixin):
    header_class = XMFHeader
    chunk_class = XMFChunk
    material_class = XMFMaterial

    @classmethod
    def get_material_library(cls, src_path):
        return cls.read_xml(f'{src_path}/libraries/material_library.xml')

    def get_header(self, stream):
        logger.info('\nget_header()')
        header = self.header_class.from_stream(stream)
        if not (header.file_type == b'XUMF' and header.version == 3 and header.chunk_offset == 64):
            raise XMFException('get_header: invalid file type!')
        logger.debug('> info: %s', header)
        return header

    def get_chunks(self, stream, header):
        logger.info('\nget_chunks(ct=%s)', header.chunk_count)
        chunks = []
        for i in range(header.chunk_count):
            logger.debug('> unpacking chunk %d', i)
            chunk = self.chunk_class.from_stream(stream, read_len=header.chunk_size)
            logger.debug('>> %s', chunk)
            chunks.append(chunk)
        return chunks

    def get_materials(self, stream, header):
        logger.info('\nget_materials(ct=%s)', header.material_count)
        materials = []
        for i in range(header.material_count):
            logger.debug('> unpacking material %d', i)
            mat = self.material_class.from_stream(stream)
            mat.name = mat.name.rstrip(b'\x00').decode('utf-8')
            logger.debug('>> material: %s', mat)
            materials.append(mat)
        return materials

    def read_chunk_data(self, stream, chunks):
        logger.info('\nread_chunk_data(ct=%d)', len(chunks))
        self.vertices = []
        self.faces = []
        self.flags = set()
        start_offset = stream.tell()
        for chunk in chunks:
            logger.debug('> reading chunk: %s', chunk)
            stream.seek(start_offset + chunk.offset)
            chunk_stream = BytesIO(zlib.decompress(stream.read(chunk.packed)))

            data_class = chunk.get_chunk_data_class()
            self.flags.update(data_class.flags)
            read_len = max(chunk.bytes, data_class.struct_len)
            data_count = chunk.qty * chunk.bytes // read_len
            from_stream = data_class.from_stream
            if VERTEX in data_class.flags:
                data = self.vertices
            else:
                data = self.faces

            logger.debug('>> info: data_class=%s, read_len=%d, data_count=%d',
                         data_class.class_name, read_len, data_count)
            for i in range(data_count):
                data.append(from_stream(stream=chunk_stream, read_len=read_len))

    def find_texture(self, mat_xml, mat_type):
        texture_name = mat_xml.find(f'./property[@name="{mat_type}"]')
        if texture_name is None:
            return None
        value = texture_name.get("value").replace('\\', '/')
        if os.path.exists(f'{self.src_path}/{value}.gz'):
            return f'{self.src_path}/{value}.gz'
        elif os.path.exists(f'{self.src_path}/{value}.dds'):
            return f'{self.src_path}/{value}.dds'

    def read_texture(self, texture_filename):
        texture_name = texture_filename.rsplit('/', 1)[1]
        texture_data = open(texture_filename, 'rb').read()
        if texture_filename.endswith('.gz'):
            texture_data = gzip.decompress(texture_data)
            texture_name = texture_name[:-3] + '.dds'
        return texture_name, texture_data

    def write_texture(self, texture_name, texture_data):
        if not os.path.exists(f'{self.obj_path}/tex/{texture_name}'):
            os.makedirs(f'{self.obj_path}/tex', exist_ok=True)
            with open(f'{self.obj_path}/tex/{texture_name}', 'wb') as out_file:
                out_file.write(texture_data)

    def add_texture(self, mat_file, mat_xml, mat_type, mtl_tag):
        texture_filename = self.find_texture(mat_xml, mat_type)
        if not texture_filename:
            return
        texture_name, texture_data = self.read_texture(texture_filename)
        self.write_texture(texture_name, texture_data)
        mat_file.write(f'{mtl_tag} ../tex/{texture_name}\n'.encode('ascii'))

    def write_material_data(self, mat_file, mat_name):
        collection, name = mat_name.split('.')
        mat_xml = self.mat_lib_xml.find(f'./collection[@name="{collection}"]/material[@name="{name}"]/properties')

        mat_file.write(f'newmtl {mat_name}\n\n'.encode('ascii'))
        mat_file.write(b'Ka 0.00 0.00 0.00\n')
        mat_file.write(b'Kd 1.00 1.00 1.00\n')
        mat_file.write(b'Ks 1.00 1.00 1.00\n')
        mat_file.write(b'Ns 4.0\n')
        mat_file.write(b'illum 2\n')

        if mat_xml is not None:
            self.add_texture(mat_file, mat_xml, 'diffuse_map', 'map_Kd')
            self.add_texture(mat_file, mat_xml, 'smooth_map', 'map_Ks')
            self.add_texture(mat_file, mat_xml, 'normal_map', 'norm')
            self.add_texture(mat_file, mat_xml, 'Metallness', 'map_Pm')

        mat_file.write(b'\n\n')

    def write_material_file(self):
        logger.info('\nwrite_material_file()')
        os.makedirs(f'{self.obj_path}/{self.file_dir}', exist_ok=True)
        with open(f'{self.obj_path}/{self.file_dir}/{self.file_name}.mat', 'wb') as mat_file:
            for material in self.materials:
                logger.debug('> write_material_data(%s)', material)
                self.write_material_data(mat_file, material.name)

    def write_vertices(self, obj_file):
        has_normals = NORMAL in self.flags
        has_uvs = UV in self.flags
        vertices = []
        normals = [b'\n']
        uvs = [b'\n']
        bad_uv = False
        for o in self.vertices:
            vertices.append(f'v {(-o.x):.3f} {o.y:.3f} {o.z:.3f}\n'.encode('ascii'))
            if has_normals:
                normals.append(f'vn {(127.5-o.nz)/127.5:.3f} {(o.ny-127.5)/127.5:.3f} {(o.nx-127.5)/127.5:.3f}\n'
                               .encode('ascii'))
            if has_uvs:
                uvs.append(f'vt {o.tu:.3f} {1.0-o.tv:.3f}\n'.encode('ascii'))
                if abs(o.tu) > 20000:
                    bad_uv = True
        if bad_uv:
            # when uvs are unpacked in incorrect format these values are out of range
            raise XMFException('Invalid UVs')

        obj_file.writelines(vertices)
        if has_normals:
            obj_file.writelines(normals)
        if has_uvs:
            obj_file.writelines(uvs)

    def write_faces(self, obj_file):
        obj_file.write(b'\n')
        if self.materials:
            for i, mat in enumerate(self.materials):
                obj_file.write(f'g group{i}\n'.encode('ascii'))
                obj_file.write(f'usemtl {mat.name}\n'.encode('ascii'))
                for f in self.faces[mat.start//3: mat.start+mat.count//3]:
                    obj_file.write(f'f {f.i0+1}/{f.i0+1}/{f.i0+1} '
                                   f'{f.i1+1}/{f.i1+1}/{f.i1+1} '
                                   f'{f.i2+1}/{f.i2+1}/{f.i2+1}\n'.encode('ascii'))
                obj_file.write(b'\n')
        else:
            for f in self.faces:
                obj_file.write(f'f {f.i0+1} {f.i1+1} {f.i2+1}\n'.encode('ascii'))

    def write_object_file(self):
        logger.info('\nwrite_object_file()')
        os.makedirs(f'{self.obj_path}/{self.file_dir}', exist_ok=True)
        with open(f'{self.obj_path}/{self.file_dir}/{self.file_name}.obj', 'wb') as obj_file:
            obj_file.write(f'mtllib {self.file_name}.mat\n'.encode('ascii'))
            logger.debug('> write_vertices()')
            self.write_vertices(obj_file)
            logger.debug('> write_faces()')
            self.write_faces(obj_file)

    def gen_thumb(self):
        logger.info('\ngen_thumb()')
        img = Image.new("RGB", (900, 315), "#FFFFFF")
        draw = ImageDraw.Draw(img)

        # ~random colors generator
        colors = ((((i*64621)**2) % 256, (((i*12415)**4) % 256), (((i*834793)*3) % 256)) for i in range(256))

        # draw grid lines
        for c in range(0, 900//150*5):
            i = c*(150.0/5)
            draw.line([i, 0, i, 300], fill=(192, 192, 192))

        for c in range(0, 300//150*5):
            i = c*(150.0/5)
            draw.line([0, i, 900, i], fill=(192, 192, 192))

        draw.line([0, 150, 900, 150], fill=(0, 0, 0))
        draw.line([150, 0, 150, 300], fill=(0, 0, 0))
        draw.line([450, 0, 450, 300], fill=(0, 0, 0))
        draw.line([750, 0, 750, 300], fill=(0, 0, 0))

        draw.line([300, 0, 300, 300], fill=(255, 255, 255))
        draw.line([600, 0, 600, 300], fill=(255, 255, 255))

        # calculate the extents of all the vertices (to figure out how to scale the object, and to display object size)
        max_extent = 0.0
        extents = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        for v in self.vertices:
            extents[0][0] = min(extents[0][0], v.x)
            extents[0][1] = max(extents[0][1], v.x)
            extents[1][0] = min(extents[1][0], v.y)
            extents[1][1] = max(extents[1][1], v.y)
            extents[2][0] = min(extents[2][0], v.z)
            extents[2][1] = max(extents[2][1], v.z)
            max_extent = max(max_extent, abs(v.x), abs(v.y), abs(v.z))

        extents[0][2] = extents[0][1] - extents[0][0]
        extents[1][2] = extents[1][1] - extents[1][0]
        extents[2][2] = extents[2][1] - extents[2][0]

        # draw all the object faces in 3 different views, grouped by materials/colors
        for mat in self.materials:
            # get ~random color
            color = next(colors)

            # draw all the faces for a given material/color
            for f in self.faces[mat.start//3: mat.start//3 + mat.count//3]:
                verts = [self.vertices[f.i0], self.vertices[f.i1], self.vertices[f.i2]]

                # draw faces in X/Y plane
                pos = [(150+150*v.x//max_extent, 150-150*v.y//max_extent) for v in verts]
                draw.polygon(pos, fill=color)

                # draw faces in X/Z plane
                pos = [(450+150*v.x//max_extent, 150+150*v.z//max_extent) for v in verts]
                draw.polygon(pos, fill=color)

                # draw faces in Y/Z plane
                pos = [(750-150*v.y//max_extent, 150+150*v.z//max_extent) for v in verts]
                draw.polygon(pos, fill=color)

        # display the object size on the image
        s = 'SIZE: %0.1fm x %0.1fm x %0.1fm' % (
            extents[0][2],
            extents[1][2],
            extents[2][2]
        )
        s += ' | SQR SIZE: %0.1fm' % (max_extent/5)
        draw.text((3, 303), s, fill=(0, 0, 0))

        # write the image to file
        os.makedirs(self.thumb_path, exist_ok=True)
        img.save(f'{self.thumb_path}/{self.file_dir}.gif', "GIF")
        return extents

    def read(self):
        logger.info('read()')
        if self.mat_lib_xml is None:
            self.mat_lib_xml = self.get_material_library(src_path=self.src_path)

        with open(self.xmf_filename, 'rb') as stream:
            self.header = self.get_header(stream=stream)
            self.chunks = self.get_chunks(stream=stream, header=self.header)
            self.materials = self.get_materials(stream=stream, header=self.header)
            self.read_chunk_data(stream=stream, chunks=self.chunks)

        self.write_object_file()
        self.write_material_file()

    def __init__(self, xmf_filename, src_path, obj_path, thumb_path, mat_lib_xml=None):
        self.xmf_filename = xmf_filename
        file_dir, file_name = xmf_filename.rsplit('/', 2)[1:]
        self.file_dir = file_dir[:-5]
        self.file_name = file_name[:-4]
        self.src_path = src_path
        self.obj_path = obj_path
        self.thumb_path = thumb_path
        self.mat_lib_xml = mat_lib_xml
        self.header = None
        self.flags = None
        self.chunks = None
        self.materials = None
        self.vertices = None
        self.faces = None


if __name__ == '__main__':
    logger.addHandler(logging.StreamHandler())

    args = set(sys.argv[1:])
    if not args:
        print("%s <path/to/file.xmf | --all>", sys.argv[0])

    elif sys.argv[1] == '--all':
        logger.setLevel(logging.ERROR)
        config = get_config()
        mat_lib_xml = XMFReader.get_material_library(src_path=config.SRC)
        files = sorted(glob.glob(config.SRC + '/assets/units/*/ship_*_data/*_main-lod0.xmf'))
        for filename in files:
            if 'part_main' in filename or 'anim_main' in filename:
                reader = XMFReader(xmf_filename=filename, mat_lib_xml=mat_lib_xml,
                                   src_path=config.SRC, obj_path=config.OBJS, thumb_path=config.THUMBS)
                try:
                    reader.read()
                    reader.gen_thumb()
                    print(f'processing {filename}.. successful!')
                except XMFException as e:
                    print(f'processing {filename}.. failed!')
                    print(f'\t\t{e}')

    else:
        logger.setLevel(logging.INFO)
        filename = sys.argv[1]
        if not filename.endswith('.xmf'):
            # if not provided a full path including name, try to find
            pattern = (f'{filename}**/*_main-lod0.xmf' if filename.endswith('/') else
                       f'{filename}*/**_main-lod0.xmf')
            search = glob.glob(pattern)
            if len(search) == 1:
                filename = search[0]
            else:
                # if none found, or too many found, print and quit
                print(f'invalid name: {filename} search results: {(len(search))}')
                filename = None

        if filename:
            config = get_config()
            reader = XMFReader(xmf_filename=filename,
                               src_path=config.SRC, obj_path=config.OBJS, thumb_path=config.THUMBS)
            reader.read()
            reader.gen_thumb()
