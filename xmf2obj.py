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

logger = logging.getLogger('x4.' + __name__)

if sys.version_info.major < 3 or sys.version_info.minor < 6:
    logger.error('This script requires python 3.6 or higher.')
    exit(0)

import os
import zlib
from io import BytesIO
from struct import unpack
from x4lib import get_config


class Chunk(object):
    def __init__(self, id1, part, offset, id2, packed, qty, bytes):
        self.id1, self.part, self.offset, self.id2, self.packed, self.qty, self.bytes = \
            id1, part, offset, id2, packed, qty, bytes
        self.unpacked = qty * bytes
        self.vertices = []
        self.faces = []

    def __str__(self):
        return f'(id1={self.id1:2}, id2={self.id2:2}, part={self.part:2}, offset={self.offset:4}, qty={self.qty:3}, ' \
               f'bytes={self.bytes:2}, packed={self.packed:4}, unpacked={self.unpacked:5})'


class Material(object):
    def __init__(self, start, count, name):
        self.start, self.count, self.name = start, count, name.rstrip(b'\x00').decode('utf-8')

    def __str__(self):
        return f'(start={self.start:3}, count={self.count:3}, name={self.name})'


def read_xmf(name, data, obj_path):
    file_type, version, chunk_offset, chunk_count, chunk_size, material_count, vertex_count, index_count = \
        unpack(b'<4shhBBB3xII42x', data.read(64))

    assert file_type == b'XUMF' and version == 3 and chunk_offset == 64, 'invalid file type!'

    logger.info('header(chunk_count=%s, chunk_size=%s, material_count=%s, vertex_count=%s, index_count=%s)',
                chunk_count, chunk_size, material_count, vertex_count, index_count)

    chunks = []
    for i in range(chunk_count):
        logger.debug('unpacking chunk %d', i)
        chunk = Chunk(*unpack('<III8xIIII', data.read(36)))
        data.seek(chunk_size-36, 1)
        chunks.append(chunk)

    materials = []
    for i in range(material_count):
        logger.debug('unpacking material %d', i)
        material = Material(*unpack('<II128s', data.read(8+128)))
        materials.append(material)

    vertices = []
    faces = []
    normals = []
    uvs = []

    start_offset = data.tell()
    for chunk in chunks:
        logger.debug('reading chunk: %s', chunk)
        data.seek(start_offset + chunk.offset)
        chunk_data = BytesIO(zlib.decompress(data.read(chunk.packed)))

        if chunk.id1 == 0 and chunk.id2 == 2 and chunk.bytes == 12:
            # vertex (f, f, f) 12 bytes
            for i in range(chunk.qty):
                x, y, z = unpack('<fff', chunk_data.read(12))
                vertices.append((-x,y,z))

        elif chunk.id1 == 0 and chunk.id2 == 32 and chunk.bytes >= 24:
            # vertex (3x4f), normal (3x1+1), tangent (3x1+1), uv (2x2)
            for i in range(chunk.qty):
                x, y, z, nx, ny, nz, tx, ty, tz, u, v = unpack('<fffBBBxBBBxee', chunk_data.read(24))
                vertices.append((-x,y,z))
                normals.append(((127-nz)/128,(ny-127)/128,(nx-127)/128))
                uvs.append((u, v))
                chunk_data.seek(chunk.bytes - 24, 1)

        elif chunk.id1 == 30 and chunk.id2 == 30 and chunk.bytes == 2:
            for i in range(chunk.qty//3):
                i0, i1, i2 = unpack('<hhh', chunk_data.read(6))
                faces.append((i0+1, i1+1, i2+1))

        elif chunk.id1 == 30 and chunk.id2 == 31 and chunk.bytes == 4:
            for i in range(chunk.qty//3):
                i0, i1, i2 = unpack('<iii', chunk_data.read(12))
                faces.append((i0+1, i1+1, i2+1))

        else:
            logger.error('unknown type id1=%r id2=%r bytes=%r', chunk.id1, chunk.id2, chunk.bytes)
            exit(0)

    logger.info('vertices: %d', len(vertices))
    logger.info('faces: %d', len(faces))
    logger.info('materials: %d', len(materials))

    if materials:
        logger.info('writing materials file')
        os.makedirs(f'{obj_path}/{name}', exist_ok=True)
        with open(f'{obj_path}/{name}/model.mat', 'wb') as of:
            for mat in materials:
                logger.debug('writing material: %s', mat)
                of.write(f'newmtl {mat.name}\n\n'.encode('ascii'))
                of.write(b'Ka 0.00 0.00 0.00\n')
                of.write(b'Kd 1.00 1.00 1.00\n')
                of.write(b'Ks 1.00 1.00 1.00\n')
                of.write(b'Ns 4.0\n')
                of.write(b'illum 2\n')
                of.write(f'map_Kd tex/{mat.name}_diff.tga\n'.encode('ascii'))
                of.write(f'map_Kd tex/{mat.name}_spec.tga\n'.encode('ascii'))
                of.write(f'map_Kd tex/{mat.name}_bump.tga\n'.encode('ascii'))
                of.write(b'\n\n')

    logger.info('writing obj file')
    with open(f'{obj_path}/{name}/model.obj', 'wb') as of:
        logger.debug('writing vertices')
        for v in vertices:
            of.write('v {:.3f} {:.3f} {:.3f} 1.0\n'.format(*v).encode('ascii'))

        of.write(b'\n')

        logger.debug('writing normals')
        for vn in normals:
            of.write('vn {:.3f} {:.3f} {:.3f}\n'.format(*vn).encode('ascii'))

        of.write(b'\n')

        logger.debug('writing uvs')
        for uv in uvs:
            of.write('vt {:.3f} {:.3f}\n'.format(*uv).encode('ascii'))

        of.write(b'\n')

        logger.debug('writing faces')
        if materials:
            for i, mat in enumerate(materials):
                of.write(f'g group{i}\n'.encode('ascii'))
                of.write(f'usemtl {mat.name}\n'.encode('ascii'))
                for f in faces[mat.start//3: mat.start+mat.count//3]:
                    of.write('f {0}/{0}/{0} {1}/{1}/{1} {2}/{2}/{2}\n'.format(*f).encode('ascii'))

                of.write(b'\n')

        else:
            for f in faces:
                of.write('f {0}/{0}/{0} {1}/{1}/{1} {2}/{2}/{2}\n'.format(*f).encode('ascii'))


if __name__ == '__main__':
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)

    args = set(sys.argv[1:])
    if not args:
        logger.info("%s <path/to/file.xmf>", sys.argv[0])
    else:
        xmf_filename = sys.argv[1]
        file_pointer = open(xmf_filename, 'rb')
        name = xmf_filename.rsplit('/', 2)[1][:-5]
        config = get_config()
        read_xmf(name, file_pointer, obj_path=config.OBJS)
