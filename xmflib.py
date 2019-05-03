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
    defaults = None

    def __init__(self, **kwargs):
        self.__dict__.update(self.defaults or {}, **kwargs)
        missing_fields = set(self.fields) - set(self.__dict__)
        if missing_fields:
            raise StructException(f'Missing fields:\n\tpassed: {kwargs}, \n\t'
                                  f'required: {self.fields}\n\t'
                                  f'missing: {missing_fields}')

    @classmethod
    def from_stream(cls, stream, read_len=0):
        obj = cls(**{k: v for k, v in zip(cls.fields, cls.struct.unpack(stream.read(cls.struct_len)))})
        stream.seek(max(0, read_len - obj.struct_len), 1)
        return obj

    def to_stream(self, write_len=0):
        data = self.struct.pack(*(self.__dict__[f] for f in self.fields))
        return data + b'\x00'*max(0, write_len-self.struct_len)

    def __repr__(self):
        return '%s(%s)' % (self.class_name, ', '.join('%s=%r' % (f, self.__dict__[f]) for f in self.fields))


class XMFException(Exception):
    pass


class XMFHeader(StructObjBase, metaclass=StructObjBaseMeta):
    fields = 'file_type,version,chunk_offset,chunk_count,chunk_size,material_count,' \
             'u1,u2,u3,vertex_count,index_count,u4,u5'
    struct_format = b'<4shhBBB3BII2I34x'
    defaults = dict(file_type=b'XUMF', version=3, chunk_offset=64, chunk_size=188, u1=136, u2=1, u3=0, u4=4, u5=0)


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
    struct_format = '<fffBBBxBBBxee'
    defaults = dict(tx=0, ty=0, tz=0)


class ChunkDataF30(StructObjBase, metaclass=StructObjBaseMeta):
    flags = {FACE}
    fields = 'i0,i1,i2'
    struct_format = '<HHH'


class ChunkDataF31(StructObjBase, metaclass=StructObjBaseMeta):
    flags = {FACE}
    fields = 'i0,i1,i2'
    struct_format = '<III'


class XMFChunk(StructObjBase, metaclass=StructObjBaseMeta):
    fields = 'id1,part,offset,one1,id2,packed,qty,bytes,one2'
    struct_format = b'<IIII4xIIIII'
    defaults = dict(one1=1, one2=1, part=0)
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
