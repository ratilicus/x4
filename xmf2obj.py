#!/usr/bin/python3.7

"""
Extract xmf files into Wavefront objs (that can be opened in 3D cad software like Blender
Use: python3.7 xmf2obj.py {path/to/filename.xmf}

Extracting should put the object files inside PWD/objs/{model name}/model.obj

python 3.6+ required

XUMF reading logic based on: https://github.com/hhrhhr/Lua-utils-for-X-Rebirth/blob/master/
"""

import sys
import logging
import os
import zlib
import glob
from io import BytesIO
from x4lib import get_config, StructObjBase, StructObjBaseMeta

logger = logging.getLogger('x4.' + __name__)

if sys.version_info.major < 3 or sys.version_info.minor < 6:
    logger.error('This script requires python 3.6 or higher.')
    exit(0)


VERTEX = 'v'
NORMAL = 'vn'
UV = 'vt'
FACE = 'f'


class XMFHeader(StructObjBase, metaclass=StructObjBaseMeta):
    fields = 'file_type,version,chunk_offset,chunk_count,chunk_size,material_count,vertex_count,index_count'
    struct_format = b'<4shhBBB3xII42x'


class ChunkDataV2(StructObjBase, metaclass=StructObjBaseMeta):
    flags = {VERTEX}
    fields = 'x,y,z'
    struct_format = '<fff'


class ChunkDataV32(StructObjBase, metaclass=StructObjBaseMeta):
    flags = {VERTEX, NORMAL, UV}
    fields = 'x,y,z,nx,ny,nz,tx,ty,tz,tu,tv'
    struct_format = '<fffBBBxBBBxff'


class ChunkDataV28(StructObjBase, metaclass=StructObjBaseMeta):
    flags = {VERTEX, NORMAL, UV}
    fields = 'x,y,z,nx,ny,nz,tx,ty,tz,tu,tv'
    struct_format = '<fffBBBxBBBxff'


class ChunkDataF30(StructObjBase, metaclass=StructObjBaseMeta):
    flags = {FACE}
    fields = 'i0,i1,i2'
    struct_format = '<HHH'


class ChunkDataF31(StructObjBase, metaclass=StructObjBaseMeta):
    flags = {FACE}
    fields = 'i0,i1,i2'
    struct_format = '<III'


class XMFChunk(StructObjBase, metaclass=StructObjBaseMeta):
    fields = 'id1,part,offset,id2,packed,qty,bytes'
    struct_format = b'<III8xIIII'

    @classmethod
    def get_data_class(cls, chunk):
        logger.debug('get_reader: chunk', chunk)
        if chunk.id1 == 0 and chunk.id2 == 2:
            reader_class = ChunkDataV2

        elif chunk.id1 == 0 and chunk.id2 == 32 and chunk.bytes >=28:
            if chunk.bytes >= 32:
                reader_class = ChunkDataV32
            else:
                reader_class = ChunkDataV28

        elif chunk.id1 == 30 and chunk.id2 == 30:
            reader_class = ChunkDataF30

        elif chunk.id1 == 30 and chunk.id2 == 31:
            reader_class = ChunkDataF31

        else:
            raise Exception(f'unknown format: id1={chunk.id1}, id2={chunk.id2}, bytes={chunk.bytes}')

        return reader_class

    def init(self, stream, chunk_size):
        stream.seek(chunk_size - self.struct_len, 1)
        self.data_class = self.get_data_class(chunk=self)
        self.unpacked = self.qty * self.bytes
        self.read_len = max(self.bytes, self.data_class.struct_len)
        self.skip_bytes = max(0, self.bytes - self.data_class.struct_len)
        self.data = []

    def read(self, stream):
        obj = self.data_class(stream)
        stream.seek(self.skip_bytes, 1)
        return obj


class XMFMaterial(StructObjBase, metaclass=StructObjBaseMeta):
    fields = 'start,count,name'
    struct_format = b'<II128s'

    def init(self, stream):
        self.name = self.name.rstrip(b'\x00').decode('utf-8')


class XMFReader(object):
    header_class = XMFHeader
    chunk_class = XMFChunk
    material_class = XMFMaterial

    def read_header(self):
        header = self.header_class(self.stream)
        assert header.file_type == b'XUMF' and header.version == 3 and header.chunk_offset == 64, 'invalid file type!'
        logger.debug('read_header', header)
        self.header = header

    def get_chunks(self):
        self.chunks = []
        for i in range(self.header.chunk_count):
            logger.debug('unpacking chunk %d', i)
            self.chunks.append(self.chunk_class(self.stream, chunk_size=self.header.chunk_size))

    def get_materials(self):
        self.materials = []
        for i in range(self.header.material_count):
            logger.debug('unpacking material %d', i)
            self.materials.append(self.material_class(self.stream))

    def read_chunk_data(self):
        self.flags = set()
        start_offset = self.stream.tell()
        for chunk in self.chunks:
            self.flags.update(chunk.data_class.flags)
            self.stream.seek(start_offset + chunk.offset)
            chunk_stream = BytesIO(zlib.decompress(self.stream.read(chunk.packed)))
            for i in range(0, chunk.unpacked, chunk.read_len):
                chunk.data.append(chunk.read(chunk_stream))

    def write_material_data(self, of, material):
        of.write(f'newmtl {material.name}\n\n'.encode('ascii'))
        of.write(b'Ka 0.00 0.00 0.00\n')
        of.write(b'Kd 1.00 1.00 1.00\n')
        of.write(b'Ks 1.00 1.00 1.00\n')
        of.write(b'Ns 4.0\n')
        of.write(b'illum 2\n')
        of.write(f'map_Kd tex/{material.name}_diff.tga\n'.encode('ascii'))
        of.write(f'map_Kd tex/{material.name}_spec.tga\n'.encode('ascii'))
        of.write(f'map_Kd tex/{material.name}_bump.tga\n'.encode('ascii'))
        of.write(b'\n\n')

    def write_material_file(self):
        logger.info('writing materials file')
        os.makedirs(f'{self.obj_path}/{self.file_dir}', exist_ok=True)
        with open(f'{self.obj_path}/{self.file_dir}/{self.file_name}.mat', 'wb') as of:
            for material in self.materials:
                self.write_material_data(of, material)

    def write_chunk_vertices(self, of, chunk):
        has_normals = NORMAL in self.flags
        has_uvs = UV in self.flags
        vertices, normals, uvs = [], [b'\n'], [b'\n']
        bad_uv = False
        maxu, minu = -20000, 20000
        for o in chunk.data:
            vertices.append(f'v {(-o.x):.3f} {o.y:.3f} {o.z:.3f}\n'.encode('ascii'))
            if has_normals:
                normals.append(f'vn {(127-o.nz)/128:.3f} {(o.ny-127)/128:.3f} {(o.nx-127)/128:.3f}\n'.encode('ascii'))
            if has_uvs:
                uvs.append(f'vt {o.tu:.3f} {1.0-o.tv:.3f}\n'.encode('ascii'))
                if abs(o.tu) > 20000:
                    bad_uv = True
                    if o.tu > maxu: maxu = o.tu
                    if o.tu < minu: minu = o.tu
        if bad_uv:
            # when uvs are unpacked in incorrect format these values are out of range
            print(f'\tINVALID UVs ({minu} - {maxu})')
            raise

        of.writelines(vertices)
        if has_normals:
            of.writelines(normals)
        if has_uvs:
            of.writelines(uvs)

    def write_chunk_faces(self, of, chunk):
        of.write(b'\n')
        if self.materials:
            for i, mat in enumerate(self.materials):
                of.write(f'g group{i}\n'.encode('ascii'))
                of.write(f'usemtl {mat.name}\n'.encode('ascii'))
                for f in chunk.data[mat.start//3: mat.start+mat.count//3]:
                    of.write(f'f {f.i0+1}/{f.i0+1}/{f.i0+1} {f.i1+1}/{f.i1+1}/{f.i1+1} {f.i2+1}/{f.i2+1}/{f.i2+1}\n'
                             .encode('ascii'))
                of.write(b'\n')
        else:
            for f in chunk.data:
                of.write(f'f {f.i0+1} {f.i1+1} {f.i2+1}\n'.encode('ascii'))

    def write_object_file(self):
        logger.info('writing obj file')
        os.makedirs(f'{self.obj_path}/{self.file_dir}', exist_ok=True)
        with open(f'{self.obj_path}/{self.file_dir}/{self.file_name}.obj', 'wb') as of:
            for chunk in self.chunks:
                if VERTEX in chunk.data_class.flags:
                    self.write_chunk_vertices(of, chunk)
                elif FACE in chunk.data_class.flags:
                    self.write_chunk_faces(of, chunk)

    def read(self):
        self.read_header()
        self.get_chunks()
        self.get_materials()
        self.read_chunk_data()
        self.write_object_file()
        self.write_material_file()

    def __init__(self, xmf_filename, obj_path):
        self.file_path, file_dir, file_name = xmf_filename.rsplit('/', 2)
        self.file_dir = file_dir[:-5]
        self.file_name = file_name[:-4]
        self.obj_path = obj_path
        self.stream = open(xmf_filename, 'rb')
        self.header = None
        self.materials = []
        self.chunks = []
        self.data = {}
        self.formatters = None


if __name__ == '__main__':
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)

    args = set(sys.argv[1:])
    if not args:
        logger.info("%s <path/to/file.xmf | --all>", sys.argv[0])

    elif sys.argv[1] == '--all':
        logger.setLevel(logging.ERROR)
        config = get_config()
        files = sorted(glob.glob('src/assets/units/*/ship_*_data/*_main-lod0.xmf'))
        for filename in files:
            if 'part_main' in filename or 'anim_main' in filename:
                reader = XMFReader(xmf_filename=filename, obj_path=config.OBJS)
                try:
                    reader.read()
                    print(f'processing {filename}.. successful!')
                except Exception as e:
                    print(f'processing {filename}.. failed!')

    else:
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
            reader = XMFReader(xmf_filename=filename, obj_path=config.OBJS)
            reader.read()
