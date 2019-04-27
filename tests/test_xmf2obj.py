"""
Run tests
Use: ./run_tests.sh
"""
import struct
from io import BytesIO
from unittest import TestCase
from unittest.mock import patch, MagicMock
from xmf2obj import XMFHeader, XMFChunk, XMFMaterial, XMFReader, StructObjBase, StructObjBaseMeta, \
    ChunkDataV2, ChunkDataV32, ChunkDataV28, ChunkDataF30, ChunkDataF31


class XMFHeaderUnitTest(TestCase):
    structobj_class = XMFHeader

    def test_baseclass(self):
        self.assertEqual(self.structobj_class.__bases__, (StructObjBase,))

    def test_fields(self):
        self.assertEqual(
            self.structobj_class.fields,
            'file_type,version,chunk_offset,chunk_count,chunk_size,material_count,vertex_count,index_count'.split(','))

    def test_struct_format(self):
        self.assertEqual(self.structobj_class.struct_format, b'<4shhBBB3xII42x')


class XMFChunkUnitTest(TestCase):
    structobj_class = XMFChunk

    def test_baseclass(self):
        self.assertEqual(self.structobj_class.__bases__, (StructObjBase,))

    def test_fields(self):
        self.assertEqual(
            self.structobj_class.fields,
            'id1,part,offset,id2,packed,qty,bytes'.split(','))

    def test_struct_format(self):
        self.assertEqual(self.structobj_class.struct_format, b'<III8xIIII')

    def test_get_data_class_V2(self):
        self.assertEqual(XMFChunk.get_data_class(MagicMock(id1=0, id2=2)), ChunkDataV2)

    def test_get_data_class_V32(self):
        self.assertEqual(XMFChunk.get_data_class(MagicMock(id1=0, id2=32, bytes=32)), ChunkDataV32)

    def test_get_data_class_V28(self):
        self.assertEqual(XMFChunk.get_data_class(MagicMock(id1=0, id2=32, bytes=28)), ChunkDataV28)

    def test_get_data_class_F30(self):
        self.assertEqual(XMFChunk.get_data_class(MagicMock(id1=30, id2=30)), ChunkDataF30)

    def test_get_data_class_F31(self):
        self.assertEqual(XMFChunk.get_data_class(MagicMock(id1=30, id2=31)), ChunkDataF31)

    def test_get_data_class_other(self):
        with self.assertRaises(Exception):
            XMFChunk.get_data_class(MagicMock(id1=2, id2=2))

    def test_init(self):
        stream = BytesIO(struct.pack('<III8xIIII64s', 0, 0, 123, 2, 54321, 101, 15, b'\x00'))
        chunk = XMFChunk(stream, chunk_size=64)
        self.assertEqual(chunk.data_class, ChunkDataV2)
        self.assertEqual(chunk.unpacked, 101*15)
        self.assertEqual(chunk.read_len, 15)
        self.assertEqual(chunk.skip_bytes, 15-12)
        self.assertEqual(chunk.data, [])
        self.assertEqual(stream.tell(), 64)

    def test_read(self):
        stream = BytesIO(struct.pack('<III8xIIII64s', 0, 0, 123, 2, 54321, 101, 12, b'\x00'))
        chunk = XMFChunk(stream, chunk_size=64)
        stream = BytesIO(struct.pack('<fff', 0.123, 0.456, 0.789))
        v2 = chunk.read(stream)
        self.assertAlmostEqual(v2.x, 0.123)
        self.assertAlmostEqual(v2.y, 0.456)
        self.assertAlmostEqual(v2.z, 0.789)
        self.assertEqual(stream.tell(), 12)



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

    def test_mat(self):
        mat = XMFMaterial(BytesIO(b'\x01\x00\x00\x00\x09\x00\x00\x00some-mat-name'+b'\x00'*128))
        self.assertEqual(mat.start, 1)
        self.assertEqual(mat.count, 9)
        self.assertEqual(mat.name, 'some-mat-name')  # verif \x00 stripped off, and converted to unicode


class XMFReaderUnitTest(TestCase):
    pass

