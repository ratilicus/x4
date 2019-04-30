"""
Run tests
Use: ./run_tests.sh
"""

from io import BytesIO
from unittest import TestCase
from unittest.mock import patch, call, MagicMock

from x4lib import require_python_version, get_config, ModUtilMixin, StructException, StructObjBaseMeta, StructObjBase


class X4LibUnitTest(TestCase):

    @patch('x4lib.sys')
    def test_require_python_version(self, patch_sys):
        patch_sys.version_info.major = 3
        patch_sys.version_info.minor = 4
        require_python_version(3, 3)

    @patch('x4lib.sys')
    def test_require_python_version_bad(self, patch_sys):
        patch_sys.version_info.major = 3
        patch_sys.version_info.major = 2
        with self.assertRaises(SystemExit):
            require_python_version(3, 3)

    @patch('builtins.__import__')
    def test_get_config(self, patch_import):
        self.assertEqual(get_config(), patch_import.return_value)
        patch_import.assert_called_once_with('config')

    @patch('builtins.__import__')
    def test_get_config_dne(self, patch_import):
        # test if config does not exist
        patch_import.side_effect = ImportError
        with self.assertRaises(SystemExit):
            get_config()

        patch_import.assert_called_once_with('config')


class ModUtilMixinUnitTest(TestCase):

    @patch('x4lib.deepcopy')
    def test_clone(self, patch_deepcopy):
        xml = MagicMock()
        self.assertEqual(ModUtilMixin.clone(xml), patch_deepcopy.return_value)
        patch_deepcopy.assert_called_once_with(xml)

    @patch('x4lib.ElementTree')
    def test_read_xml(self, patch_ET):
        filepath = 'file-path'
        self.assertEqual(ModUtilMixin.read_xml(filepath=filepath), patch_ET.parse.return_value)
        patch_ET.parse.assert_called_once_with(filepath)

    @patch('x4lib.ElementTree')
    def test_read_xml_raises_error(self, patch_ET):
        patch_ET.parse.side_effect = Exception
        filepath = 'file-path'
        with self.assertRaises(Exception):
            ModUtilMixin.read_xml(filepath=filepath)
        patch_ET.parse.assert_called_once_with(filepath)

    @patch('x4lib.ElementTree')
    def test_read_xml_allow_faii(self, patch_ET):
        patch_ET.parse.side_effect = Exception
        filepath = 'file-path'
        self.assertEqual(ModUtilMixin.read_xml(filepath=filepath, allow_fail=True), None)
        patch_ET.parse.assert_called_once_with(filepath)

    @patch('x4lib.ModUtilMixin.read_xml')
    def test_get_macros(self, patch_read_xml):
        patch_read_xml.return_value.findall.return_value = [
            {'name': 'macro1', 'value': 'path\\to\\macro1.xml'},
            {'name': 'macro2', 'value': 'path\\to\\macro2.xml'},
        ]
        src_path = 'src-path'
        self.assertEqual(ModUtilMixin.get_macros(src_path=src_path), {
            'macro1': 'path/to/macro1.xml',
            'macro2': 'path/to/macro2.xml',
        })
        patch_read_xml.assert_called_once_with(src_path+'/index/macros.xml')
        patch_read_xml.return_value.findall.assert_called_once_with('./entry')

    @patch('x4lib.ModUtilMixin.read_xml')
    def test_get_components(self, patch_read_xml):
        patch_read_xml.return_value.findall.return_value = [
            {'name': 'component1', 'value': 'path\\to\\component1.xml'},
            {'name': 'component2', 'value': 'path\\to\\component2.xml'},
        ]
        src_path = 'src-path'
        self.assertEqual(ModUtilMixin.get_components(src_path=src_path), {
            'component1': 'path/to/component1.xml',
            'component2': 'path/to/component2.xml',
        })
        patch_read_xml.assert_called_once_with(src_path+'/index/components.xml')
        patch_read_xml.return_value.findall.assert_called_once_with('./entry')

    @patch('x4lib.ModUtilMixin.read_xml')
    def test_get_wares(self, patch_read_xml):
        src_path = 'src-path'
        self.assertEqual(ModUtilMixin.get_wares(src_path=src_path), patch_read_xml.return_value)
        patch_read_xml.assert_called_once_with(src_path+'/libraries/wares.xml', allow_fail=False)

    @patch('x4lib.ModUtilMixin.read_xml')
    def test_get_wares_allow_fail(self, patch_read_xml):
        src_path = 'src-path'
        self.assertEqual(ModUtilMixin.get_wares(src_path=src_path, allow_fail=True), patch_read_xml.return_value)
        patch_read_xml.assert_called_once_with(src_path+'/libraries/wares.xml', allow_fail=True)

    @patch('builtins.open')
    @patch('x4lib.csv')
    def test_read_csv(self, patch_csv, patch_open):
        patch_csv.reader.return_value = [
            ('H component-1', 'f1', 'f2', 'f3'),
            ('#', 'some ignored comment'),
            ('D', 'v11', '', 'v13'),
            ('', 'another ignored line'),
            ('D', '', 'v22', ''),
            ('',),
            ('H component-2', 'f21', 'f22', ''),
            ('D', 'v211', 'v212', ''),
            ('D', 'v221', '', ''),
            ('D', '', 'v232', ''),
        ]
        filename = 'path/to/file.csv'
        csv_data = {}
        ModUtilMixin.read_csv(filename, csv_data)
        self.assertEqual(csv_data, {
            'component-1': [
                {'f1': 'v11', 'f2': '', 'f3': 'v13'},
                {'f1': '', 'f2': 'v22', 'f3': ''}],
            'component-2': [
                {'f21': 'v211', 'f22': 'v212'},
                {'f21': 'v221', 'f22': ''},
                {'f21': '', 'f22': 'v232'}
            ]
        })
        patch_csv.reader.assert_called_once_with(patch_open.return_value)
        patch_open.assert_called_once_with(filename)

    @patch('builtins.open')
    @patch('x4lib.os')
    def test_write_xml(self, patch_os, patch_open):
        filename = 'path/to/filename'
        xml = MagicMock()
        ModUtilMixin.write_xml(filename, xml)
        patch_open.assert_called_once_with(filename, 'wb')
        xml.write.assert_called_once_with(
            patch_open.return_value.__enter__.return_value, encoding='utf-8', xml_declaration=True)
        patch_os.path.dirname.assert_called_once_with(filename)
        patch_os.makedirs.assert_called_once_with(patch_os.path.dirname.return_value, exist_ok=True)

    def test_set_xml(self):
        xml = MagicMock()
        path = './xml/element/path'
        key = 'attr-name'
        value_template = MagicMock()
        row = {'a': 1, 'b': 2}
        label = 'label-for-error'
        self.assertEqual(
            ModUtilMixin.set_xml(xml=xml, path=path, key=key, value_template=value_template, row=row, label=label),
            True)
        xml.find.assert_called_once_with(path)
        xml.find.return_value.set.assert_called_once_with(key, value_template.format.return_value)
        value_template.format.assert_called_once_with(**row)

    @patch('x4lib.ElementTree')
    def test_set_xml_find_fail(self, patch_ET):
        xml = MagicMock()
        xml.find.return_value = None
        path = './xml/element/path'
        key = 'attr-name'
        value_template = MagicMock()
        row = {'a': 1, 'b': 2}
        label = 'label-for-error'
        with self.assertRaises(SystemExit):
            ModUtilMixin.set_xml(xml=xml, path=path, key=key, value_template=value_template, row=row, label=label)

        xml.find.assert_called_once_with(path)

    def test_set_xml_value_template_error(self):
        xml = MagicMock()
        path = './xml/element/path'
        key = 'attr-name'
        value_template = MagicMock()
        value_template.format.side_effect = Exception
        row = {'a': 1, 'b': 2}
        label = 'label-for-error'
        with self.assertRaises(SystemExit):
            ModUtilMixin.set_xml(xml=xml, path=path, key=key, value_template=value_template, row=row, label=label)

        xml.find.assert_called_once_with(path)
        value_template.format.assert_called_once_with(**row)

    @patch('x4lib.ModUtilMixin.set_xml')
    def test_update_xml(self, patch_set_xml):
        xml = MagicMock()
        row = MagicMock()
        mapping = [
            ('.xml/path/el-1', 'attr-1', 'tpl-str-1'),
            ('.xml/pathel-2', 'attr-2', 'tpl-str-2'),
        ]
        label = MagicMock()
        ModUtilMixin.update_xml(xml=xml, row=row, mapping=mapping, label=label)
        self.assertEqual(patch_set_xml.call_count, 2)
        patch_set_xml.assert_has_calls([
            call(xml, mapping[0][0], mapping[0][1], mapping[0][2], row, label=label),
            call(xml, mapping[1][0], mapping[1][1], mapping[1][2], row, label=label),
        ])


class TestObj(StructObjBase, metaclass=StructObjBaseMeta):
    fields = 'text,short,int'
    struct_format = b'<3shi'


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