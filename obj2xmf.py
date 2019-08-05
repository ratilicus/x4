#!/usr/bin/env python3.7

"""
Write Wavefront objs into xmf files
Use: python3.7 obj2xmf.py {path/to/filename.obj}

python 3.6+ required

XUMF reading logic based on: https://github.com/hhrhhr/Lua-utils-for-X-Rebirth/blob/master/
"""

import sys
import logging
import zlib
from io import BytesIO

from math import sqrt

from lib.x4lib import get_config, require_python_version
from lib.xmflib import XMFHeader, XMFChunk, XMFMaterial, ChunkDataV32, ChunkDataF31, VERTEX, NORMAL, UV

require_python_version(3, 6)
logger = logging.getLogger('x4.' + __name__)

# These values are required when writing the xmf file (they probably indicate the chunk data structs + other stuff)
chunk0_extra = b'\x05\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x03\x00\xe1\x0d\x04\x00\x00\x00\x06\x00\x00\x00\x01\x00\x00\x00\x05\x00\x15\x40\x04\x00\x00\x00\x0a\x00\x00\x00\x04\x00\x00\x00\x0a\x00\x00\x0d\x00\x00\x00\x00\x0a\x00\x00\x00\x00\x00\x00\x00\x17\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0f\x00\x00\x00\x00\x00\x00\x00\xb0\xf1\xe0\x0d\x00\x00\x00\x00\xd6\x05\xd8\x57\xff\x7f\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xb0\xf1\x00\x0d'
chunk1_extra = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xe0\x94\x86\x40\x00\x00\x00\x00\x0f\x00\x00\x00\x00\x00\x00\x00\x60\xf7\xe0\x0d\x00\x00\x00\x00\xb9\xf7\xe0\x0d\x00\x00\x00\x00\xd6\x05\xd8\x57\xff\x7f\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0f\x00\x00\x00\x00\x00\x00\x00\xfe\xff\xff\xff\xff\xff\xff\xff\x00\x00\xe0\x0d\x00\x00\x00\x00\xc8\xf7\xe0\x0d\x00\x00\x00\x00\x31\x82\x11\x40\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xe0\x94\x86\x40\x00\x00\x00\x00\x40\xdb\x3f\x2b\x00\x00\x00\x00\xb9\xf7\xe0\x0d'


def cross(ax, ay, az, bx, by, bz):
    # cross product
    cx = ay*bz - az*by
    cy = az*bx - ax*bz
    cz = ax*by - ay*bx
    return cx, cy, cz


def calc_tan(v1, v2, v3):
    # obj files don't contain tangent data (doesn't seem necessary, but probably affects specular lighting of model)
    # http://www.terathon.com/code/tangent.html
    nx = v1.nxf
    ny = v1.nyf
    nz = v1.nzf

    x1 = -v2.x + v1.x
    x2 = -v3.x + v1.x
    y1 = v2.y - v1.y
    y2 = v3.y - v1.y
    z1 = v2.z - v1.z
    z2 = v3.z - v1.z

    s1 = v2.tu - v1.tu
    s2 = v3.tu - v1.tu
    t1 = -v2.tv + v1.tv
    t2 = -v3.tv + v1.tv

    if (s1 * t2 - s2 * t1) == 0.0:
        return
    r = 1.0 / (s1 * t2 - s2 * t1)

    t1x = (t2 * x1 - t1 * x2) * r
    t1y = (t2 * y1 - t1 * y2) * r
    t1z = (t2 * z1 - t1 * z2) * r

    t2x = (s1 * x2 - s2 * x1) * r
    t2y = (s1 * y2 - s2 * y1) * r
    t2z = (s1 * z2 - s2 * z1) * r

    dot1 = nx * t1x + ny * t1y + nz * t1z
    tx = t1x - nx * dot1
    ty = t1y - ny * dot1
    tz = t1z - nz * dot1
    l = sqrt(tx*tx + ty*ty + tz*tz)
    tx /= l
    ty /= l
    tz /= l

    cpx, cpy, cpz = cross(nx, ny, nz, t1x, t1y, t1z)
    dot2 = cpx * t2x + cpy * t2y + cpz * t2z
    if dot2 < 0.0:
        tx *= -1
        ty *= -1
        tz *= -1

    v1.tx = v2.tx = v3.tx = x = max(0, int(127 + 128 * tz))
    v1.ty = v2.ty = v3.ty = y = max(0, int(127 + 128 * ty))
    v1.tz = v2.tz = v3.tz = z = max(0, int(127 - 128 * tx))


class XMFWriter(object):
    header_class = XMFHeader
    chunk_class = XMFChunk
    material_class = XMFMaterial
    vertex_class = ChunkDataV32
    face_class = ChunkDataF31

    def get_vertex(self, vtn_str, obj_data, vertex_indexes):
        vtn = tuple(map(lambda v: int(v) - 1, vtn_str.split('/')))
        if vtn in vertex_indexes:
            vi = vertex_indexes[vtn]
            v = self.vertices[vi]
        else:
            vertex_indexes[vtn] = vi = len(self.vertices)
            x, y, z = obj_data[VERTEX][vtn[0]]
            tu, tv = obj_data[UV][vtn[1]]
            nx, ny, nz = obj_data[NORMAL][vtn[2]]
            v = self.vertex_class(
                x=-x, y=y, z=z,
                tu=tu, tv=1.0-tv,
                nx=max(0, int(127+128*nz)),
                ny=max(0, int(127+128*ny)),
                nz=max(0, int(127-128*nx)),
                nxf=nx,
                nyf=ny,
                nzf=nz)
            self.vertices.append(v)
        return v, vi

    def read_obj(self, lines):
        self.materials = []
        self.vertices = []
        vertex_indexes = {}
        mat_name = None
        mat_start = 0
        obj_data = {VERTEX: [], NORMAL: [], UV: []}

        for i, line in enumerate(lines):
            t, *values = line.strip().split(' ')
            if t in (VERTEX, NORMAL, UV):
                obj_data[t].append(tuple(float(val) for val in values))

            elif t == 'f':
                v0, vi0 = self.get_vertex(vtn_str=values[0], obj_data=obj_data, vertex_indexes=vertex_indexes)
                v1, vi1 = self.get_vertex(vtn_str=values[1], obj_data=obj_data, vertex_indexes=vertex_indexes)
                v2, vi2 = self.get_vertex(vtn_str=values[2], obj_data=obj_data, vertex_indexes=vertex_indexes)
                # calc_tan(v0, v1, v2)
                self.faces.append(self.face_class(i0=vi0, i1=vi1, i2=vi2))

            elif t == 'usemtl':
                if mat_name:
                    count = len(self.faces)-mat_start
                    self.materials.append(self.material_class(name=mat_name.encode('ascii'),
                                                              start=mat_start*3, count=count*3))
                mat_name = '.'.join(values[0].split('.')[:2])
                mat_start = len(self.faces)

        if mat_name:
            count = len(self.faces) - mat_start
            self.materials.append(self.material_class(name=mat_name.encode('ascii'),
                                                      start=mat_start*3, count=count*3))

    def write_xmf(self, stream):
        header = self.header_class(chunk_count=2, material_count=len(self.materials),
                                   vertex_count=len(self.vertices), index_count=len(self.faces)*3)

        print()
        print(stream.tell(), header)
        stream.write(header.to_stream())

        data_bytes = 32
        chunk_stream = BytesIO()
        for v in self.vertices:
            chunk_stream.write(v.to_stream(write_len=data_bytes))
        unpacked_len = chunk_stream.tell()
        qty = unpacked_len // data_bytes
        chunk_stream.seek(0)
        chunk0_data = zlib.compress(chunk_stream.read())
        chunk0_packed_len = len(chunk0_data)
        chunk = self.chunk_class(id1=0, id2=32, bytes=data_bytes, qty=qty,
                                 offset=0, packed=chunk0_packed_len,
                                 extra_data=chunk0_extra)
        print()
        print(f'bytes={data_bytes}, qty={qty}, unpacked={unpacked_len}, packed={chunk0_packed_len}')
        print(stream.tell(), chunk)
        stream.write(chunk.to_stream(write_len=header.chunk_size))

        data_bytes = 4
        chunk_stream = BytesIO()
        for f in self.faces:
            chunk_stream.write(f.to_stream(write_len=data_bytes))
        unpacked_len = chunk_stream.tell()
        qty = unpacked_len // data_bytes
        chunk_stream.seek(0)
        chunk1_data = zlib.compress(chunk_stream.read())
        chunk1_packed_len = len(chunk1_data)
        chunk = self.chunk_class(id1=30, id2=31, bytes=data_bytes, qty=qty,
                                 offset=chunk0_packed_len, packed=chunk1_packed_len,
                                 extra_data=chunk1_extra)
        print()
        print(f'bytes={data_bytes}, qty={qty}, unpacked={unpacked_len}, packed={chunk1_packed_len}')
        print(stream.tell(), chunk)
        stream.write(chunk.to_stream(write_len=header.chunk_size))

        print()
        for mat in self.materials:
            print(stream.tell(), mat)
            stream.write(mat.to_stream())

        print()
        print(stream.tell(), f'writing chunk0 packed data: {chunk0_packed_len}')
        stream.write(chunk0_data)
        print(stream.tell(), f'writing chunk1 packed data: {chunk1_packed_len}')
        stream.write(chunk1_data)

    def write(self):
        logger.info('write()')
        with open(self.obj_filename, 'r') as lines:
            self.read_obj(lines)

        with open(self.obj_filename+'.xmf', 'wb') as of:
            self.write_xmf(of)

    def __init__(self, obj_filename):
        self.obj_filename = obj_filename
        self.xmf_filename = obj_filename + '.xmf'
        self.materials = []
        self.vertices = []
        self.faces = []


if __name__ == '__main__':
    logger.addHandler(logging.StreamHandler())

    args = set(sys.argv[1:])
    if not args:
        print("%s <path/to/file.xmf | --all>", sys.argv[0])

    else:
        logger.setLevel(logging.INFO)
        filename = sys.argv[1]
        config = get_config()
        reader = XMFWriter(obj_filename=filename)
        reader.write()
