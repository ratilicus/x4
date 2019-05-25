"""
Run tests
Use: ./run_tests.sh
"""

from io import BytesIO
from unittest import TestCase

from lib.xmflib import StructException, StructObjBaseMeta, StructObjBase, XMFHeader, XMFChunk, XMFMaterial, XMFException,\
    ChunkDataV2, ChunkDataV32, ChunkDataV28, ChunkDataF30, ChunkDataF31


class TestObj(StructObjBase, metaclass=StructObjBaseMeta):
    fields = 'text,short,int'
    struct_format = b'<3shi'
    defaults = dict(text=b'default')


class StructObjUnitTest(TestCase):
    def test_metaclass_struct_len(self):
        self.assertEqual(TestObj.struct_len, 3+2+4)

    def test_init(self):
        obj = TestObj(text='some-text', short=1234, int=5678, extra_kwarg=1000)
        self.assertEqual(obj.text, 'some-text')
        self.assertEqual(obj.short, 1234)
        self.assertEqual(obj.int, 5678)
        self.assertEqual(obj.extra_kwarg, 1000)
        self.assertEqual(str(obj), "TestObj(text='some-text', short=1234, int=5678)")

    def test_init_missing_kwarg(self):
        with self.assertRaises(StructException):
            TestObj(text='some-text', int=5678, extra_kwarg=1000)

    def test_from_stream(self):
        stream = BytesIO(b'ABC\x01\x00\x02\x00\x00\x00DEF\x03\x00\x04\x00\x00\x00')
        obj = TestObj.from_stream(stream)
        self.assertEqual(obj.text, b'ABC')
        self.assertEqual(obj.short, 1)
        self.assertEqual(obj.int, 2)
        self.assertEqual(str(obj), "TestObj(text=b'ABC', short=1, int=2)")
        self.assertEqual(stream.tell(), obj.struct_len)

        obj = TestObj.from_stream(stream)
        self.assertEqual(obj.text, b'DEF')
        self.assertEqual(obj.short, 3)
        self.assertEqual(obj.int, 4)
        self.assertEqual(str(obj), "TestObj(text=b'DEF', short=3, int=4)")
        self.assertEqual(stream.tell(), obj.struct_len*2)

    def test_from_stream_with_read_len(self):
        stream = BytesIO(b'ABC\x01\x00\x02\x00\x00\x00DEF\x03\x00\x04\x00\x00\x00')
        obj = TestObj.from_stream(stream, read_len=TestObj.struct_len+3)
        self.assertEqual(obj.text, b'ABC')
        self.assertEqual(obj.short, 1)
        self.assertEqual(obj.int, 2)
        self.assertEqual(str(obj), "TestObj(text=b'ABC', short=1, int=2)")
        self.assertEqual(stream.tell(), obj.struct_len+3)

    def test_to_stream(self):
        obj = TestObj(text=b'some-text', short=3, int=9)
        self.assertEqual(obj.to_stream(), b'som\x03\x00\t\x00\x00\x00')


class XMFHeaderUnitTest(TestCase):
    structobj_class = XMFHeader

    def test_baseclass(self):
        self.assertEqual(self.structobj_class.__bases__, (StructObjBase,))

    def test_fields(self):
        self.assertEqual(
            self.structobj_class.fields,
            'file_type,version,chunk_offset,chunk_count,chunk_size,material_count,' \
            'u1,u2,u3,vertex_count,index_count,u4,u5'.split(','))

    def test_struct_format(self):
        self.assertEqual(self.structobj_class.struct_format, b'<4shhBBB3BII2I34x')


class XMFChunkUnitTest(TestCase):
    structobj_class = XMFChunk

    def test_baseclass(self):
        self.assertEqual(self.structobj_class.__bases__, (StructObjBase,))

    def test_fields(self):
        self.assertEqual(
            self.structobj_class.fields,
            'id1,part,offset,one1,id2,packed,qty,bytes,one2,extra_data'.split(','))

    def test_struct_format(self):
        self.assertEqual(self.structobj_class.struct_format, b'<IIII4xIIIII16x132s')

    def test_get_chunk_data_class_V2(self):
        chunk = XMFChunk(id1=0, id2=2, bytes=12, part=0, offset=0, packed=0, qty=0)
        self.assertEqual(chunk.get_chunk_data_class(), ChunkDataV2)

    def test_get_chunk_data_class_V32(self):
        chunk = XMFChunk(id1=0, id2=32, bytes=32, part=0, offset=0, packed=0, qty=0)
        self.assertEqual(chunk.get_chunk_data_class(), ChunkDataV32)

    def test_get_chunk_data_class_V28(self):
        chunk = XMFChunk(id1=0, id2=32, bytes=28, part=0, offset=0, packed=0, qty=0)
        self.assertEqual(chunk.get_chunk_data_class(), ChunkDataV28)

    def test_get_chunk_data_class_F30(self):
        chunk = XMFChunk(id1=30, id2=30, bytes=12, part=0, offset=0, packed=0, qty=0)
        self.assertEqual(chunk.get_chunk_data_class(), ChunkDataF30)

    def test_get_chunk_data_class_F31(self):
        chunk = XMFChunk(id1=30, id2=31, bytes=12, part=0, offset=0, packed=0, qty=0)
        self.assertEqual(chunk.get_chunk_data_class(), ChunkDataF31)

    def test_get_data_class_other(self):
        with self.assertRaises(XMFException):
            chunk = XMFChunk(id1=2, id2=2, bytes=12, part=0, offset=0, packed=0, qty=0)
            chunk.get_chunk_data_class()


class XMFMaterialUnitTest(TestCase):
    structobj_class = XMFMaterial

    def test_baseclass(self):
        self.assertEqual(self.structobj_class.__bases__, (StructObjBase,))

    def test_fields(self):
        self.assertEqual(
            self.structobj_class.fields,
            'start,count,name'.split(','))

    def test_struct_format(self):
        self.assertEqual(self.structobj_class.struct_format, b'<II128s')
