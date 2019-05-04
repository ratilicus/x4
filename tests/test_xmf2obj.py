"""
Run tests
Use: ./run_tests.sh
"""
import struct
from io import BytesIO
from unittest import TestCase
from unittest.mock import patch, call, MagicMock
from xmflib import ChunkDataV2, ChunkDataV28, ChunkDataF31, VERTEX, NORMAL, UV
from xmf2obj import XMFException, XMFChunk, XMFMaterial, XMFReader


class XMFReaderUnitTest(TestCase):
    def setUp(self) -> None:
        self.reader = XMFReader(xmf_filename='path/to/src/assets/ship_blah_data/part_main-lod0.xmf',
                                src_path='path/to/src', obj_path='path/to/objs', thumb_path='path/to/thumbs',
                                mat_lib_xml=MagicMock())

    @patch('xmf2obj.XMFReader.read_xml')
    def test_get_material_library(self, patch_read_xml):
        src_path = 'some/src/path'
        self.assertEqual(XMFReader.get_material_library(src_path), patch_read_xml.return_value)
        patch_read_xml.assert_called_once_with(f'{src_path}/libraries/material_library.xml')

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

    @patch('xmf2obj.os.path.exists')
    def test_find_texture_mat_not_found_in_mat_xml(self, patch_os_path_exists):
        mat_xml = MagicMock()
        mat_xml.find.return_value = None
        mat_type = 'diffuse_map'
        self.assertEqual(self.reader.find_texture(mat_xml, mat_type), None)
        mat_xml.find.assert_called_once_with(f'./property[@name="{mat_type}"]')
        self.assertEqual(patch_os_path_exists.call_count, 0)

    @patch('xmf2obj.os.path.exists', side_effect=[True])
    def test_find_texture_gz_exists(self, patch_os_path_exists):
        mat_xml = MagicMock()
        mat_xml.find.return_value = {'value': 'assets\\path\\to\\file'}
        mat_type = 'diffuse_map'
        self.assertEqual(self.reader.find_texture(mat_xml, mat_type),
                         f'{self.reader.src_path}/assets/path/to/file.gz')
        mat_xml.find.assert_called_once_with(f'./property[@name="{mat_type}"]')
        self.assertEqual(patch_os_path_exists.call_count, 1)
        patch_os_path_exists.assert_called_once_with(f'{self.reader.src_path}/assets/path/to/file.gz')

    @patch('xmf2obj.os.path.exists', side_effect=[False, True])
    def test_find_texture_dds_exists(self, patch_os_path_exists):
        mat_xml = MagicMock()
        mat_xml.find.return_value = {'value': 'assets\\path\\to\\file'}
        mat_type = 'diffuse_map'
        self.assertEqual(self.reader.find_texture(mat_xml, mat_type),
                         f'{self.reader.src_path}/assets/path/to/file.dds')
        mat_xml.find.assert_called_once_with(f'./property[@name="{mat_type}"]')
        self.assertEqual(patch_os_path_exists.call_count, 2)
        patch_os_path_exists.assert_has_calls([
            call(f'{self.reader.src_path}/assets/path/to/file.gz'),
            call(f'{self.reader.src_path}/assets/path/to/file.dds'),
        ])

    @patch('xmf2obj.os.path.exists', side_effect=[False, False])
    def test_find_texture_none_exist(self, patch_os_path_exists):
        mat_xml = MagicMock()
        mat_xml.find.return_value = {'value': 'assets\\path\\to\\file'}
        mat_type = 'diffuse_map'
        self.assertEqual(self.reader.find_texture(mat_xml, mat_type), None)
        mat_xml.find.assert_called_once_with(f'./property[@name="{mat_type}"]')
        self.assertEqual(patch_os_path_exists.call_count, 2)
        patch_os_path_exists.assert_has_calls([
            call(f'{self.reader.src_path}/assets/path/to/file.gz'),
            call(f'{self.reader.src_path}/assets/path/to/file.dds'),
        ])

    @patch('builtins.open')
    def test_read_texture(self, patch_open):
        texture_filename = 'src/assets/textures/multimat/multimat_02_diff.dds'
        self.assertEqual(self.reader.read_texture(texture_filename),
                         ('multimat_02_diff.dds', patch_open.return_value.read.return_value))
        patch_open.assert_called_once_with(texture_filename, 'rb')
        patch_open.return_value.read.assert_called_once_with()

    @patch('xmf2obj.gzip')
    @patch('builtins.open')
    def test_read_texture_compressed(self, patch_open, patch_gzip):
        texture_filename = 'src/assets/textures/multimat/multimat_02_diff.gz'
        self.assertEqual(self.reader.read_texture(texture_filename),
                         ('multimat_02_diff.dds', patch_gzip.decompress.return_value))
        patch_gzip.decompress.assert_called_once_with(patch_open.return_value.read.return_value)
        patch_open.assert_called_once_with(texture_filename, 'rb')
        patch_open.return_value.read.assert_called_once_with()

    @patch('xmf2obj.os.path.exists', return_value=True)
    @patch('builtins.open')
    def test_write_texture_already_exists(self, patch_open, patch_os_path_exists):
        texture_name = 'multimat_02_diff.dds'
        texture_data = MagicMock()
        self.reader.write_texture(texture_name, texture_data)
        patch_os_path_exists.assert_called_once_with(f'{self.reader.obj_path}/tex/{texture_name}')
        self.assertEqual(patch_open.call_count, 0)

    @patch('xmf2obj.os')
    @patch('builtins.open')
    def test_write_texture_new(self, patch_open, patch_os):
        patch_os.path.exists.return_value = False
        texture_name = 'multimat_02_diff.dds'
        texture_data = MagicMock()
        self.reader.write_texture(texture_name, texture_data)
        patch_os.path.exists.assert_called_once_with(f'{self.reader.obj_path}/tex/{texture_name}')
        patch_os.makedirs(f'{self.reader.obj_path}/tex', exist_ok=True)
        patch_open.assert_called_once_with(f'{self.reader.obj_path}/tex/{texture_name}', 'wb')
        patch_open.return_value.__enter__.return_value.write.assert_called_once_with(texture_data)

    def test_add_texture(self):
        mat_file = MagicMock()
        mat_xml = MagicMock()
        self.reader.find_texture = MagicMock(return_value='src/assets/textures/multimat/multimat_02_diff.gz')
        self.reader.read_texture = MagicMock(return_value=('multimat_02_diff.dds', 'some-texture-data'))
        self.reader.write_texture = MagicMock()

        self.reader.add_texture(mat_file, mat_xml, 'diff', 'map_Kd')
        self.reader.find_texture.assert_called_once_with(mat_xml, 'diff')
        self.reader.read_texture.assert_called_once_with('src/assets/textures/multimat/multimat_02_diff.gz')
        self.reader.write_texture.assert_called_once_with('multimat_02_diff.dds', 'some-texture-data')
        mat_file.write.assert_called_once_with(b'map_Kd ../tex/multimat_02_diff.dds\n')

    def test_add_texture_none_found(self):
        mat_file = MagicMock()
        mat_xml = MagicMock()
        self.reader.find_texture = MagicMock(return_value=None)
        self.reader.read_texture = MagicMock()
        self.reader.write_texture = MagicMock()

        self.reader.add_texture(mat_file, mat_xml, 'diff', 'map_Kd')
        self.reader.find_texture.assert_called_once_with(mat_xml, 'diff')
        self.assertEqual(self.reader.read_texture.call_count, 0)
        self.assertEqual(self.reader.write_texture.call_count, 0)
        self.assertEqual(mat_file.write.call_count, 0)

    def test_write_material_data(self):
        self.reader.add_texture = MagicMock()
        mat_name = 'p1.multimat'
        mat_file = MagicMock()
        self.reader.write_material_data(mat_file, mat_name)
        self.assertEqual(mat_file.write.call_count, 7)
        mat_file.assert_has_calls([
            call.write(b'newmtl p1.multimat\n\n'),
            call.write(b'Ka 0.00 0.00 0.00\n'),
            call.write(b'Kd 1.00 1.00 1.00\n'),
            call.write(b'Ks 1.00 1.00 1.00\n'),
            call.write(b'Ns 4.0\n'),
            call.write(b'illum 2\n'),
            call.write(b'\n\n'),
        ])
        self.assertEqual(self.reader.add_texture.call_count, 4)
        self.reader.add_texture.assert_has_calls([
            call(mat_file, self.reader.mat_lib_xml.find.return_value, 'diffuse_map', 'map_Kd'),
            call(mat_file, self.reader.mat_lib_xml.find.return_value, 'smooth_map', 'map_Ks'),
            call(mat_file, self.reader.mat_lib_xml.find.return_value, 'normal_map', 'norm'),
            call(mat_file, self.reader.mat_lib_xml.find.return_value, 'Metallness', 'map_Pm'),
        ])
        self.reader.mat_lib_xml.find.assert_called_once_with(
            './collection[@name="p1"]/material[@name="multimat"]/properties')

    @patch('xmf2obj.os')
    @patch('builtins.open')
    def test_write_material_file(self, patch_open, patch_os):
        self.reader.write_material_data = MagicMock()
        self.reader.materials = [
            XMFMaterial(name=b'mat1', start=0, count=10),
            XMFMaterial(name=b'mat2', start=10, count=10),
            XMFMaterial(name=b'mat3', start=20, count=10),
        ]
        self.reader.write_material_file()
        patch_os.makedirs.assert_called_once_with(f'{self.reader.obj_path}/{self.reader.file_dir}', exist_ok=True)
        patch_open.assert_called_once_with(
            f'{self.reader.obj_path}/{self.reader.file_dir}/{self.reader.file_name}.mat', 'wb')
        self.reader.write_material_data.assert_has_calls([
            call(patch_open.return_value.__enter__.return_value, b'mat1'),
            call(patch_open.return_value.__enter__.return_value, b'mat2'),
            call(patch_open.return_value.__enter__.return_value, b'mat3'),
        ])

    def test_write_vertices_v2(self):
        self.reader.flags = {VERTEX}
        self.reader.vertices = [
            ChunkDataV2(x=1.1+i, y=1.2+i, z=1.3+i)
            for i in range(3)
        ]
        obj_file = BytesIO()
        self.reader.write_vertices(obj_file)

        obj_file.seek(0)
        self.assertEqual(
            obj_file.read(),
            b'v -1.100 1.200 1.300\n'
            b'v -2.100 2.200 2.300\n'
            b'v -3.100 3.200 3.300\n'
        )

    def test_write_vertices_v28(self):
        self.reader.flags = {VERTEX, NORMAL, UV}
        self.reader.vertices = [
            ChunkDataV28(x=1.1+i, y=1.2+i, z=1.3+i, nx=127.5+12.75*i, ny=12.75*i, nz=12.75*i*2, tu=1.7+i, tv=1.8+i)
            for i in range(3)
        ]
        obj_file = BytesIO()
        self.reader.write_vertices(obj_file)

        obj_file.seek(0)
        self.assertEqual(
            obj_file.read(),
            b'v -1.100 1.200 1.300\n'
            b'v -2.100 2.200 2.300\n'
            b'v -3.100 3.200 3.300\n'
            b'\n'
            b'vn 1.000 -1.000 0.000\n'
            b'vn 0.800 -0.900 0.100\n'
            b'vn 0.600 -0.800 0.200\n'
            b'\n'
            b'vt 1.700 -0.800\n'
            b'vt 2.700 -1.800\n'
            b'vt 3.700 -2.800\n'
        )

    def test_write_vertices_v28_invalid_uvs(self):
        self.reader.flags = {VERTEX, NORMAL, UV}
        self.reader.vertices = [
            ChunkDataV28(x=1.1, y=1.2, z=1.3, nx=127.5, ny=12.75, nz=12.75, tu=20001, tv=1.8)
        ]
        obj_file = MagicMock()
        with self.assertRaises(XMFException):
            self.reader.write_vertices(obj_file)

    def test_write_faces_no_materials(self):
        self.reader.materials = []
        self.reader.faces = [
            ChunkDataF31(i0=10, i1=11, i2=12),
            ChunkDataF31(i0=20, i1=21, i2=22),
            ChunkDataF31(i0=30, i1=31, i2=32),
        ]
        obj_file = BytesIO()
        self.reader.write_faces(obj_file)

        obj_file.seek(0)
        self.assertEqual(
            obj_file.read(),
            b'\n'
            b'f 11 12 13\n'
            b'f 21 22 23\n'
            b'f 31 32 33\n'
        )

    def test_write_faces_with_materials(self):
        self.reader.materials = [
            XMFMaterial(start=0, count=3*3, name='mat1'),
            XMFMaterial(start=3*3, count=2*3, name='mat2'),
        ]
        self.reader.faces = [
            ChunkDataF31(i0=i*3, i1=i*3+1, i2=i*3+2)
            for i in range(0, 5)
        ]
        obj_file = BytesIO()
        self.reader.write_faces(obj_file)

        obj_file.seek(0)
        self.assertEqual(
            obj_file.read(),
            b'\n'
            b'g group0\n'
            b'usemtl mat1\n'
            b'f 1/1/1 2/2/2 3/3/3\n'
            b'f 4/4/4 5/5/5 6/6/6\n'
            b'f 7/7/7 8/8/8 9/9/9\n'
            b'\n'
            b'g group1\n'
            b'usemtl mat2\n'
            b'f 10/10/10 11/11/11 12/12/12\n'
            b'f 13/13/13 14/14/14 15/15/15\n'
            b'\n'
        )

    @patch('xmf2obj.os')
    @patch('builtins.open')
    def test_write_object_file(self, patch_open, patch_os):
        self.reader.write_vertices = MagicMock()
        self.reader.write_faces = MagicMock()

        self.reader.write_object_file()

        patch_os.makedirs.assert_called_once_with(f'{self.reader.obj_path}/{self.reader.file_dir}', exist_ok=True)
        patch_open.assert_called_once_with(
            f'{self.reader.obj_path}/{self.reader.file_dir}/{self.reader.file_name}.obj', 'wb')

        patch_open.return_value.__enter__.return_value.write.assert_called_once_with(
            f'mtllib {self.reader.file_name}.mat\n'.encode('ascii'))
        self.reader.write_vertices.assert_called_once_with(patch_open.return_value.__enter__.return_value)
        self.reader.write_faces.assert_called_once_with(patch_open.return_value.__enter__.return_value)

    @patch('builtins.open')
    def test_read(self, patch_open):
        self.reader.get_material_library = MagicMock()
        self.reader.get_header = MagicMock()
        self.reader.get_chunks = MagicMock()
        self.reader.get_materials = MagicMock()
        self.reader.read_chunk_data = MagicMock()
        self.reader.write_object_file = MagicMock()
        self.reader.write_material_file = MagicMock()
        stream = patch_open.return_value.__enter__.return_value
        header = self.reader.get_header.return_value
        chunks = self.reader.get_chunks.return_value

        self.reader.read()

        self.assertEqual(self.reader.get_material_library.call_count, 0)
        patch_open.assert_called_once_with(self.reader.xmf_filename, 'rb')
        self.reader.get_header.assert_called_once_with(stream=stream)
        self.reader.get_chunks.assert_called_once_with(stream=stream, header=header)
        self.reader.get_materials.assert_called_once_with(stream=stream, header=header)
        self.reader.read_chunk_data.assert_called_once_with(stream=stream, chunks=chunks)
        self.reader.write_object_file.assert_called_once_with()
        self.reader.write_material_file.assert_called_once_with()

    @patch('builtins.open')
    def test_read_no_mat_lib_xml(self, patch_open):
        self.reader.mat_lib_xml = None  # test when mat_lib_xml was not passed to init
        self.reader.get_material_library = MagicMock()
        self.reader.get_header = MagicMock()
        self.reader.get_chunks = MagicMock()
        self.reader.get_materials = MagicMock()
        self.reader.read_chunk_data = MagicMock()
        self.reader.write_object_file = MagicMock()
        self.reader.write_material_file = MagicMock()

        self.reader.read()

        self.reader.get_material_library.assert_called_once_with(src_path=self.reader.src_path)

    @patch('xmf2obj.os')
    @patch('xmf2obj.ImageDraw')
    @patch('xmf2obj.Image')
    def test_gen_thumb(self, patch_image, patch_imagedraw, patch_os):
        self.reader.vertices = [
            ChunkDataV2(x=(i-7.5)*4, y=(i-4)*8, z=(i-2.0)*2)
            for i in range(16)
        ]
        self.reader.faces = [
            ChunkDataF31(i0=i*3, i1=i*3+1, i2=i*3+2)
            for i in range(0, 5)
        ]
        self.reader.materials = [
            XMFMaterial(start=0, count=3*3, name='mat1'),
            XMFMaterial(start=3*3, count=2*3, name='mat2'),
        ]

        self.assertEqual(self.reader.gen_thumb(), [
            [-30.0, 30.0, 60.0],    # x min, max, diff
            [-32, 88, 120],         # y min, max, diff
            [-4.0, 26.0, 30.0]      # z min, max, diff
        ])
        patch_os.makedirs.assert_called_once_with(self.reader.thumb_path, exist_ok=True)
        patch_imagedraw.Draw.return_value.text.assert_called_once_with(
            (3, 303), 'SIZE: 60.0m x 120.0m x 30.0m | SQR SIZE: 17.6m', fill=(0, 0, 0))
        patch_image.new.assert_called_once_with('RGB', (900, 315), '#FFFFFF')
        patch_image.new.return_value.save.assert_called_once_with(
            f'{self.reader.thumb_path}/{self.reader.file_dir}.gif', "GIF")
