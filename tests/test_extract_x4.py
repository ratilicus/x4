"""
Run tests
Use: ./run_tests.sh
"""

from unittest import TestCase
from unittest.mock import patch, call, MagicMock
from extract_x4 import extract_x4,CatParser


class ExtractX4UnitTest(TestCase):
    CAT_FILES = [
        ('some path/filename1.xml', 0, 101),
        ('some path/filename1.xml.sig', 101, 210),
        ('some path/filename2.xmf', 101 + 210, 300),
    ]

    def test_parse_line(self):
        self.assertEqual(CatParser.parse_line('file name 543210 15512345 1234567890abcdef'),
                         ('file name', 543210))

    def test_parse_line_fail(self):
        with self.assertRaises(ValueError):
            CatParser.parse_line('invalid-line')

    def test_is_script_file(self):
        self.assertTrue(CatParser.is_script_file('filename.xml'))

    def test_is_script_file_false(self):
        self.assertFalse(CatParser.is_script_file('filename.xmf'))

    def test_is_script_file_sig(self):
        self.assertFalse(CatParser.is_script_file('filename.xml.sig'))

    def test_is_sig_file(self):
        self.assertTrue(CatParser.is_sig_file('filename.xml.sig'))

    def test_is_sig_file_false(self):
        self.assertFalse(CatParser.is_sig_file('filename.xml'))

    @patch('builtins.open')
    def test_cat_files_iterator(self, patch_open):
        cat_filename = 'path/to/catfile.cat'
        patch_open.return_value.__enter__.return_value.__iter__.return_value = [
            'some path/filename1.xml 101 15512345 1234567890abcdef',
            'some path/filename1.xml.sig 210 15512345 1234567890abcdef',
            'some path/filename2.xmf 300 15512345 1234567890abcdef',
        ]
        rows = list(CatParser.cat_files_iterator(cat_filename))
        self.assertEqual(rows, self.CAT_FILES)
        patch_open.assert_called_once_with('path/to/catfile.cat', 'r')

    @patch('builtins.open')
    @patch('extract_x4.os')
    def test_extract_file(self, patch_os, patch_open):
        dat_file = MagicMock()
        out_file_path = 'dst/path/filename'
        offset = 123
        size = 456
        CatParser.extract_file(dat_file, out_file_path, offset, size)
        patch_os.makedirs.assert_called_once_with('dst/path', exist_ok=True)
        dat_file.seek.assert_called_once_with(offset)
        dat_file.read.assert_called_once_with(size)
        patch_open.assert_called_once_with(out_file_path, 'wb')
        patch_open.return_value.__enter__.return_value.write.assert_called_once_with(dat_file.read.return_value)

    @patch('extract_x4.logger')
    def test_list_scripts(self, patch_logger):
        parser = CatParser()
        parser.cat_files_iterator = MagicMock(return_value=self.CAT_FILES)
        parser.list(cat_filename='path/to/catfile.cat')
        parser.cat_files_iterator.assert_called_once_with('path/to/catfile.cat')
        patch_logger.info.assert_called_once_with('%60s (%10d)', 'some path/filename1.xml', 101)

    @patch('extract_x4.logger')
    def test_list_all_no_sig(self, patch_logger):
        parser = CatParser(scripts_only=False)
        parser.cat_files_iterator = MagicMock(return_value=self.CAT_FILES)
        parser.list(cat_filename='path/to/catfile.cat')
        parser.cat_files_iterator.assert_called_once_with('path/to/catfile.cat')
        self.assertEqual(patch_logger.info.call_count, 2)
        patch_logger.info.assert_has_calls([
            call('%60s (%10d)', 'some path/filename1.xml', 101),
            call('%60s (%10d)', 'some path/filename2.xmf', 300),
        ])

    @patch('extract_x4.logger')
    def test_list_all_inc_sig(self, patch_logger):
        parser = CatParser(scripts_only=False, signatures=True)
        parser.cat_files_iterator = MagicMock(return_value=self.CAT_FILES)
        parser.list(cat_filename='path/to/catfile.cat', )
        parser.cat_files_iterator.assert_called_once_with('path/to/catfile.cat')
        self.assertEqual(patch_logger.info.call_count, 3)
        patch_logger.info.assert_has_calls([
            call('%60s (%10d)', 'some path/filename1.xml', 101),
            call('%60s (%10d)', 'some path/filename1.xml.sig', 210),
            call('%60s (%10d)', 'some path/filename2.xmf', 300),
        ])

    @patch('builtins.open')
    def test_extract_scripts(self, patch_open):
        parser = CatParser(out_path='some/out/path')
        parser.cat_files_iterator = MagicMock(return_value=self.CAT_FILES)
        parser.extract_file = MagicMock()
        parser.extract(cat_filename='path/to/catfile.cat')
        parser.cat_files_iterator.assert_called_once_with('path/to/catfile.cat')
        patch_open.assert_called_once_with('path/to/catfile.dat', 'rb')
        parser.extract_file.assert_called_once_with(patch_open.return_value.__enter__.return_value,
                                                    'some/out/path/some path/filename1.xml', 0, 101)

    @patch('builtins.open')
    def test_extract_all_no_sig(self, patch_open):
        parser = CatParser(out_path='some/out/path', scripts_only=False)
        parser.cat_files_iterator = MagicMock(return_value=self.CAT_FILES)
        parser.extract_file = MagicMock()
        parser.extract(cat_filename='path/to/catfile.cat')
        parser.cat_files_iterator.assert_called_once_with('path/to/catfile.cat')
        patch_open.assert_called_once_with('path/to/catfile.dat', 'rb')
        self.assertEqual(parser.extract_file.call_count, 2)
        parser.extract_file.assert_has_calls([
            call(patch_open.return_value.__enter__.return_value, 'some/out/path/some path/filename1.xml', 0, 101),
            call(patch_open.return_value.__enter__.return_value, 'some/out/path/some path/filename2.xmf', 311, 300),
        ])

    @patch('builtins.open')
    def test_extract_all_inc_sig(self, patch_open):
        parser = CatParser(out_path='some/out/path', scripts_only=False, signatures=True)
        parser.cat_files_iterator = MagicMock(return_value=self.CAT_FILES)
        parser.extract_file = MagicMock()
        parser.extract(cat_filename='path/to/catfile.cat')
        parser.cat_files_iterator.assert_called_once_with('path/to/catfile.cat')
        patch_open.assert_called_once_with('path/to/catfile.dat', 'rb')
        self.assertEqual(parser.extract_file.call_count, 3)
        parser.extract_file.assert_has_calls([
            call(patch_open.return_value.__enter__.return_value, 'some/out/path/some path/filename1.xml', 0, 101),
            call(patch_open.return_value.__enter__.return_value, 'some/out/path/some path/filename1.xml.sig', 101, 210),
            call(patch_open.return_value.__enter__.return_value, 'some/out/path/some path/filename2.xmf', 311, 300),
        ])

    @patch('extract_x4.CatParser')
    @patch('extract_x4.os')
    def test_extract_x4_list(self, patch_os, patch_parser):
        config = MagicMock(X4='path/to/x4', SRC='path/to/src')
        scripts_only = MagicMock()
        signatures = MagicMock()
        patch_os.listdir.return_value = ['somefile1', 'catfile2.cat', 'catfile2.dat', 'catfile1.cat', 'catfile1.dat']
        extract_x4(config=config, extract=False, scripts_only=scripts_only, signatures=signatures)
        patch_parser.assert_called_once_with(out_path=config.SRC, scripts_only=scripts_only, signatures=signatures)
        self.assertEqual(patch_parser.return_value.list.call_count, 2)
        patch_parser.return_value.list.assert_has_calls([
            call(cat_filename='path/to/x4/catfile1.cat'),
            call(cat_filename='path/to/x4/catfile2.cat'),
        ])

    @patch('extract_x4.CatParser')
    @patch('extract_x4.os')
    def test_extract_x4_extract(self, patch_os, patch_parser):
        config = MagicMock(X4='path/to/x4', SRC='path/to/src')
        scripts_only = MagicMock()
        signatures = MagicMock()
        patch_os.listdir.return_value = ['somefile1', 'catfile2.cat', 'catfile2.dat', 'catfile1.cat', 'catfile1.dat']
        extract_x4(config=config, extract=True, scripts_only=scripts_only, signatures=signatures)
        patch_parser.assert_called_once_with(out_path=config.SRC, scripts_only=scripts_only, signatures=signatures)
        self.assertEqual(patch_parser.return_value.extract.call_count, 2)
        patch_parser.return_value.extract.assert_has_calls([
            call(cat_filename='path/to/x4/catfile1.cat'),
            call(cat_filename='path/to/x4/catfile2.cat'),
        ])