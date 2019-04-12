"""
Run tests
Use: ./run_tests.sh
"""

from unittest import TestCase
from unittest.mock import patch, call, MagicMock

from pack_x4 import pack_path


class PackX4UnitTest(TestCase):

    @patch('builtins.open')
    @patch('pack_x4.os')
    @patch('pack_x4.shutil')
    @patch('pack_x4.hashlib')
    def test_pack(self, patch_hashlib, patch_shutil, patch_os, patch_open):
        src = 'src/path/'
        dst = 'dst/path/'
        catfile, datfile, file1, file2, file3, file4 = patch_open.side_effect = [
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
        ]
        file1.read.return_value = b'file1 content 1'
        file2.read.return_value = b'file2 content 12'
        file3.read.return_value = b'file3 content 123'
        file4.read.return_value = b'file4 content 1234'
        patch_os.path.join = lambda a, b: a+'/'+b
        patch_os.walk.return_value = [
            ('src/path', [], ['cp-file']),
            ('src/path/dir_a', [], ['file1', 'file2']),
            ('src/path/dir_b', [], ['file3', 'file4']),
        ]
        patch_hashlib.md5.return_value.hexdigest.side_effect = ['hash1', 'hash2', 'hash3', 'hash4']
        patch_os.stat.side_effect = [
            MagicMock(st_mtime=1001),
            MagicMock(st_mtime=1002),
            MagicMock(st_mtime=1003),
            MagicMock(st_mtime=1004),
        ]

        pack_path(src, dst)

        # verify the correct calls are made
        patch_os.makedirs.assert_called_once_with(dst, exist_ok=True)
        patch_open.assert_has_calls([
            call('dst/path/ext_01.cat', 'wb'),
            call('dst/path/ext_01.dat', 'wb'),
            call('src/path/dir_a/file1', 'rb'),
            call('src/path/dir_a/file2', 'rb'),
            call('src/path/dir_b/file3', 'rb'),
            call('src/path/dir_b/file4', 'rb'),
        ])
        patch_os.walk.assert_called_once_with(src)
        patch_shutil.copy.assert_has_calls([
            call('src/path/cp-file', 'dst/path/cp-file'),
        ])
        patch_hashlib.md5.assert_has_calls([
            call(file1.read.return_value),
            call().hexdigest(),
            call(file2.read.return_value),
            call().hexdigest(),
            call(file3.read.return_value),
            call().hexdigest(),
            call(file4.read.return_value),
            call().hexdigest(),
        ])

        patch_os.stat.assert_has_calls([
            call('src/path/dir_a/file1'),
            call('src/path/dir_a/file2'),
            call('src/path/dir_b/file3'),
            call('src/path/dir_b/file4'),
        ])

        # verify the correct data is written to cat file
        catfile.__enter__.return_value.write.assert_has_calls([
            call(b'dir_a/file1 15 1001 hash1\n'),
            call(b'dir_a/file2 16 1002 hash2\n'),
            call(b'dir_b/file3 17 1003 hash3\n'),
            call(b'dir_b/file4 18 1004 hash4\n'),
        ])

        # verify the correct data is written to dat file
        datfile.__enter__.return_value.write.assert_has_calls([
            call(file1.read.return_value),
            call(file2.read.return_value),
            call(file3.read.return_value),
            call(file4.read.return_value),
        ])