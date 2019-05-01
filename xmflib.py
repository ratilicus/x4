"""
XMF file format support library
XUMF reading logic based on: https://github.com/hhrhhr/Lua-utils-for-X-Rebirth/blob/master/
"""

import logging
from struct import calcsize, Struct

logger = logging.getLogger('x4.' + __name__)


VERTEX = 'v'
NORMAL = 'vn'
UV = 'vt'
FACE = 'f'


class StructException(Exception):
    pass


class StructObjBaseMeta(type):
    struct_format = None

    def __init__(cls, name, bases, namespace):
        super(StructObjBaseMeta, cls).__init__(name, bases, namespace)
        cls.class_name = name
        cls.fields = cls.fields.split(',')
        cls.struct_len = calcsize(cls.struct_format)
        cls.struct = Struct(cls.struct_format)


class StructObjBase(object):
    class_name = None
    fields = None
    struct = None
    struct_len = None

    def __init__(self, **kwargs):
        if set(self.fields) - set(kwargs):
            raise StructException(f'Missing fields:\n\tpassed: {kwargs}, \n\trequired: {self.fields}')
        self.__dict__ = kwargs

    @classmethod
    def from_stream(cls, stream, read_len=0):
        obj = cls(**{k: v for k, v in zip(cls.fields, cls.struct.unpack(stream.read(cls.struct_len)))})
        stream.seek(max(0, read_len - obj.struct_len), 1)
        return obj

    def to_stream(self):
        return self.struct.pack(*(self.__dict__[f] for f in self.fields))

    def __repr__(self):
        return '%s(%s)' % (self.class_name, ', '.join('%s=%r' % (f, self.__dict__[f]) for f in self.fields))


class XMFException(Exception):
    pass


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
    id1 = None
    id2 = None
    bytes = None

    def get_chunk_data_class(self):
        if self.id1 == 0 and self.id2 == 2:
            data_class = ChunkDataV2

        elif self.id1 == 0 and self.id2 == 32 and self.bytes >= 28:
            if self.bytes >= 32:
                data_class = ChunkDataV32
            else:
                data_class = ChunkDataV28

        elif self.id1 == 30 and self.id2 == 30:
            data_class = ChunkDataF30

        elif self.id1 == 30 and self.id2 == 31:
            data_class = ChunkDataF31

        else:
            raise XMFException(f'unknown format: id1={self.id1}, id2={self.id2}, bytes={self.bytes}')
        return data_class


class XMFMaterial(StructObjBase, metaclass=StructObjBaseMeta):
    fields = 'start,count,name'
    struct_format = b'<II128s'

