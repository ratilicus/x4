"""
Run tests
Use: ./run_tests.sh
"""
import struct
from io import BytesIO
from unittest import TestCase
from unittest.mock import patch, call, MagicMock
from xmf2obj import XMFException, XMFHeader, XMFChunk, XMFMaterial, XMFReader, StructObjBase, StructObjBaseMeta, \
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


class XMFReaderUnitTest(TestCase):
    def setUp(self) -> None:
        self.reader = XMFReader(xmf_filename='path/to/src/assets/ship_blah_data/part_main-lod0.xmf',
                                obj_path='path/to/objs', thumb_path='path/to/thumbs')

    def test_file_dir(self):
        self.assertEqual(self.reader.file_dir, 'ship_blah')

    def test_file_name(self):
        self.assertEqual(self.reader.file_name, 'part_main-lod0')

    def test_obj_path(self):
        self.assertEqual(self.reader.obj_path, 'path/to/objs')

    def test_thumb_path(self):
        self.assertEqual(self.reader.thumb_path, 'path/to/thumbs')

    def test_header(self):
        self.reader.header_class = MagicMock()
        header = self.reader.header_class.from_stream.return_value
        header.file_type = b'XUMF'
        header.version = 3
        header.chunk_offset = 64
        stream = MagicMock()
        self.assertEqual(self.reader.get_header(stream=stream), header)

    def test_header_invalid(self):
        self.reader.header_class = MagicMock()
        header = self.reader.header_class.from_stream.return_value
        header.file_type = b'BLAH'
        header.version = 3
        header.chunk_offset = 64
        stream = MagicMock()
        with self.assertRaises(XMFException):
            self.reader.get_header(stream=stream)

    def test_get_chunks(self):
        self.reader.chunk_class = MagicMock()
        stream = MagicMock()
        header = MagicMock(chunk_count=2)
        self.assertEqual(self.reader.get_chunks(stream=stream, header=header), [
            self.reader.chunk_class.from_stream.return_value,
            self.reader.chunk_class.from_stream.return_value,
        ])
        self.reader.chunk_class.from_stream.assert_has_calls([
            call(stream, read_len=header.chunk_size),
            call(stream, read_len=header.chunk_size),
        ])

    def test_get_materials(self):
        self.reader.material_class = MagicMock()
        self.reader.material_class.from_stream.side_effect = materials = [
            XMFMaterial(name=b'mat1\x00\x00', start=0, count=1000),
            XMFMaterial(name=b'mat2\x00\x00', start=1000, count=500),
            XMFMaterial(name=b'mat3\x00\x00', start=1500, count=50),
        ]
        stream = MagicMock()
        header = MagicMock(material_count=3)
        self.assertEqual(self.reader.get_materials(stream=stream, header=header), [
            materials[0],
            materials[1],
            materials[2],
        ])
        self.reader.material_class.from_stream.assert_has_calls([
            call(stream),
            call(stream),
            call(stream),
        ])
        self.assertEqual(materials[0].name, 'mat1')
        self.assertEqual(materials[1].name, 'mat2')
        self.assertEqual(materials[2].name, 'mat3')

    @patch('xmf2obj.zlib')
    @patch('xmf2obj.BytesIO')
    def test_read_chunk_data(self, patch_bytesio, patch_zlib):
        chunk0 = XMFChunk(id1=0, id2=32, bytes=28, part=0, offset=100, packed=1234, qty=10)
        chunk0.get_chunk_data_class = MagicMock()
        chunk0.get_chunk_data_class.return_value.flags = ChunkDataV28.flags
        chunk0.get_chunk_data_class.return_value.struct_len = 11
        chunk0.get_chunk_data_class.return_value.from_stream.side_effect = range(1, 11)

        chunk1 = XMFChunk(id1=30, id2=31, bytes=12, part=0, offset=200, packed=5678, qty=5)
        chunk1.get_chunk_data_class = MagicMock()
        chunk1.get_chunk_data_class.return_value.flags = ChunkDataF31.flags
        chunk1.get_chunk_data_class.return_value.struct_len = 12
        chunk1.get_chunk_data_class.return_value.from_stream.side_effect = range(11, 16)
        stream = MagicMock()
        stream.tell.return_value = 101
        self.reader.read_chunk_data(stream=stream, chunks=[chunk0, chunk1])

        chunk0.get_chunk_data_class.assert_called_once_with()
        chunk0.get_chunk_data_class.return_value.from_stream.assert_has_calls([
            call(stream=patch_bytesio.return_value, read_len=28)
            for i in range(10)
        ])

        chunk1.get_chunk_data_class.assert_called_once_with()
        chunk1.get_chunk_data_class.return_value.from_stream.assert_has_calls([
            call(stream=patch_bytesio.return_value, read_len=12)
            for i in range(5)
        ])

        patch_bytesio.assert_has_calls([
            call(patch_zlib.decompress.return_value),
            call(patch_zlib.decompress.return_value),
        ])
        patch_zlib.decompress.assert_has_calls([
            call(stream.read.return_value),
            call(stream.read.return_value),
        ])
        stream.assert_has_calls([
            call.tell(),
            call.seek(101+100),
            call.read(chunk0.packed),
            call.seek(101 + 200),
            call.read(chunk1.packed),
        ])

        self.assertEqual(self.reader.vertices, list(range(1, 11)))
        self.assertEqual(self.reader.faces, list(range(11,16)))

        self.assertEqual(self.reader.flags, ChunkDataV28.flags | ChunkDataF31.flags)