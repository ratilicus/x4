"""
Run tests
Use: ./run_tests.sh
"""

from unittest import TestCase
from unittest.mock import call, patch, MagicMock
import logging
from x4 import setup_logging, cmd_extract_x4, cmd_compile_mod, cmd_pack_mod, get_parser, VERBOSITY


class PackModUnitTest(TestCase):

    @patch('x4.logging.StreamHandler')
    @patch('x4.logging.getLogger')
    def test_setup_logging(self, patch_get_logger, patch_stream_handler):
        verbosity = 2
        setup_logging(verbosity)
        patch_get_logger.assert_called_once_with()
        patch_get_logger.return_value.addHandler.assert_called_once_with(patch_stream_handler.return_value)
        patch_get_logger.return_value.setLevel.assert_called_once_with(VERBOSITY[verbosity])

    @patch('x4.logging.getLogger')
    def test_setup_logging_default(self, patch_get_logger):
        verbosity = 343
        setup_logging(verbosity)
        patch_get_logger.return_value.setLevel.assert_called_once_with(logging.WARNING)

    @patch('x4.CatParser')
    @patch('x4.get_config')
    @patch('x4.setup_logging')
    def test_cmd_extract_x4_file(self, patch_setup_logging, patch_get_config, patch_cat_parser):
        patch_get_config.return_value.PWD = '/path/to/pwd'
        patch_get_config.return_value.X4 = '/path/to/game-dir'
        args = MagicMock(file='path/to/cat-file.cat', list=False)

        cmd_extract_x4(args)

        patch_setup_logging.assert_called_once_with(args.verbosity)
        patch_cat_parser.assert_called_once_with(
            out_path='/path/to/pwd/custom',
            scripts_only=args.scripts,
            signatures=args.signatures,
        )
        patch_cat_parser.return_value.extract.assert_called_once_with(cat_filename='path/to/cat-file.cat')

    @patch('x4.glob')
    @patch('x4.CatParser')
    @patch('x4.get_config')
    @patch('x4.setup_logging')
    def test_cmd_extract_x4_extract(self, patch_setup_logging, patch_get_config, patch_cat_parser, patch_glob):
        patch_glob.iglob.return_value = [
            'path/to/02.cat',
            'path/to/01.cat',
            'path/to/03.cat',
        ]
        patch_get_config.return_value.SRC = '/path/to/src'
        patch_get_config.return_value.X4 = '/path/to/game-dir'
        args = MagicMock(file=None, list=False)

        cmd_extract_x4(args)

        patch_setup_logging.assert_called_once_with(args.verbosity)
        patch_cat_parser.assert_called_once_with(
            out_path=patch_get_config.return_value.SRC,
            scripts_only=args.scripts,
            signatures=args.signatures,
        )
        self.assertEqual(patch_cat_parser.return_value.extract.call_count, 3)
        patch_cat_parser.return_value.extract.assert_has_calls([
            call(cat_filename='path/to/01.cat'),
            call(cat_filename='path/to/02.cat'),
            call(cat_filename='path/to/03.cat'),
        ])
        patch_glob.iglob.assert_called_once_with('/path/to/game-dir/*.cat')

    @patch('x4.X4ModCompiler')
    @patch('x4.get_config')
    @patch('x4.setup_logging')
    def test_cmd_compile_mod(self, patch_setup_logging, patch_get_config, patch_compiler):
        args = MagicMock()

        cmd_compile_mod(args)

        patch_setup_logging.assert_called_once_with(args.verbosity)
        patch_compiler.assert_called_once_with(mod_name=args.mod_name, config=patch_get_config.return_value)
        patch_compiler.return_value.compile.assert_called_once_with()

    @patch('x4.pack_mod')
    @patch('x4.get_config')
    @patch('x4.setup_logging')
    def test_cmd_pack_mod(self, patch_setup_logging, patch_get_config, patch_pack_mod):
        args = MagicMock()

        cmd_pack_mod(args)

        patch_setup_logging.assert_called_once_with(args.verbosity)
        patch_pack_mod.assert_called_once_with(mod_name=args.mod_name, config=patch_get_config.return_value)

    def test_get_parser_extract_cat_file(self):
        parser = get_parser()
        args = parser.parse_args(['x', '-f' 'cat-file'])
        self.assertEqual(args.func, cmd_extract_x4)
        self.assertEqual(args.file, 'cat-file')
        self.assertEqual(args.all, False)
        self.assertEqual(args.scripts, False)
        self.assertEqual(args.list, False)
        self.assertEqual(args.signatures, False)
        self.assertEqual(args.verbosity, 1)

    def test_get_parser_extract_all(self):
        parser = get_parser()
        args = parser.parse_args(['x', '-a', '-v', '1'])
        self.assertEqual(args.func, cmd_extract_x4)
        self.assertEqual(args.file, None)
        self.assertEqual(args.all, True)
        self.assertEqual(args.scripts, False)
        self.assertEqual(args.list, False)
        self.assertEqual(args.signatures, False)
        self.assertEqual(args.verbosity, 1)

    def test_get_parser_extract_all_with_signatures(self):
        parser = get_parser()
        args = parser.parse_args(['x', '-a', '--signatures'])
        self.assertEqual(args.func, cmd_extract_x4)
        self.assertEqual(args.file, None)
        self.assertEqual(args.all, True)
        self.assertEqual(args.scripts, False)
        self.assertEqual(args.list, False)
        self.assertEqual(args.signatures, True)
        self.assertEqual(args.verbosity, 1)

    def test_get_parser_extract_scripts(self):
        parser = get_parser()
        args = parser.parse_args(['x', '-s', '-v', '2'])
        self.assertEqual(args.func, cmd_extract_x4)
        self.assertEqual(args.file, None)
        self.assertEqual(args.all, False)
        self.assertEqual(args.scripts, True)
        self.assertEqual(args.list, False)
        self.assertEqual(args.signatures, False)
        self.assertEqual(args.verbosity, 2)

    def test_get_parser_extract_list(self):
        parser = get_parser()
        args = parser.parse_args(['x', '-l', '-v', '3'])
        self.assertEqual(args.func, cmd_extract_x4)
        self.assertEqual(args.file, None)
        self.assertEqual(args.all, False)
        self.assertEqual(args.scripts, False)
        self.assertEqual(args.list, True)
        self.assertEqual(args.signatures, False)
        self.assertEqual(args.verbosity, 3)

    def test_get_parser_compile(self):
        parser = get_parser()
        args = parser.parse_args(['c', 'mod-name', '-v', '3'])
        self.assertEqual(args.func, cmd_compile_mod)
        self.assertEqual(args.mod_name, 'mod-name')
        self.assertEqual(args.verbosity, 3)

    def test_get_parser_pack(self):
        parser = get_parser()
        args = parser.parse_args(['p', 'mod-name', '-v', '2'])
        self.assertEqual(args.func, cmd_pack_mod)
        self.assertEqual(args.mod_name, 'mod-name')
        self.assertEqual(args.verbosity, 2)
