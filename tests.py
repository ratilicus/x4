from unittest import main, TestCase
from mock import patch, MagicMock

from x4lib import read_xml, get_macros, get_components, get_wares, write_xml, set_xml


class TestX4Lib(TestCase):

    @patch('x4lib.ET')
    def test_read_xml(self, patch_ET):
        filepath = 'file-path'
        self.assertEqual(read_xml(filepath=filepath), patch_ET.parse.return_value)
        patch_ET.parse.assert_called_once_with(filepath)

    @patch('x4lib.ET')
    def test_read_xml_raises_error(self, patch_ET):
        patch_ET.parse.side_effect = Exception
        filepath = 'file-path'
        with self.assertRaises(Exception):
            read_xml(filepath=filepath)
        patch_ET.parse.assert_called_once_with(filepath)

    @patch('x4lib.ET')
    def test_read_xml_allow_faii(self, patch_ET):
        patch_ET.parse.side_effect = Exception
        filepath = 'file-path'
        self.assertEqual(read_xml(filepath=filepath, allow_fail=True), None)
        patch_ET.parse.assert_called_once_with(filepath)

    @patch('x4lib.read_xml')
    def test_get_macros(self, patch_read_xml):
        patch_read_xml.return_value.findall.return_value = [
            {'name': 'macro1', 'value': 'path\\to\\macro1.xml'},
            {'name': 'macro2', 'value': 'path\\to\\macro2.xml'},
        ]
        src_path = 'src-path'
        self.assertEqual(get_macros(src_path=src_path), {
            'macro1': 'path/to/macro1.xml',
            'macro2': 'path/to/macro2.xml',
        })
        patch_read_xml.assert_called_once_with(src_path+'/index/macros.xml')
        patch_read_xml.return_value.findall.assert_called_once_with('./entry')

    @patch('x4lib.read_xml')
    def test_get_components(self, patch_read_xml):
        patch_read_xml.return_value.findall.return_value = [
            {'name': 'component1', 'value': 'path\\to\\component1.xml'},
            {'name': 'component2', 'value': 'path\\to\\component2.xml'},
        ]
        src_path = 'src-path'
        self.assertEqual(get_components(src_path=src_path), {
            'component1': 'path/to/component1.xml',
            'component2': 'path/to/component2.xml',
        })
        patch_read_xml.assert_called_once_with(src_path+'/index/components.xml')
        patch_read_xml.return_value.findall.assert_called_once_with('./entry')

    @patch('x4lib.read_xml')
    def test_get_wares(self, patch_read_xml):
        src_path = 'src-path'
        self.assertEqual(get_wares(src_path=src_path), patch_read_xml.return_value)
        patch_read_xml.assert_called_once_with(src_path+'/libraries/wares.xml', allow_fail=False)

    @patch('x4lib.read_xml')
    def test_get_wares_allow_fail(self, patch_read_xml):
        src_path = 'src-path'
        self.assertEqual(get_wares(src_path=src_path, allow_fail=True), patch_read_xml.return_value)
        patch_read_xml.assert_called_once_with(src_path+'/libraries/wares.xml', allow_fail=True)

    @patch('builtins.open')
    def test_write_xml(self, patch_open):
        filename = 'file-path-name'
        xml = MagicMock()
        write_xml(filename, xml)
        patch_open.assert_called_once_with(filename, 'wb')
        xml.write.assert_called_once_with(
            patch_open.return_value.__enter__.return_value, encoding='utf-8', xml_declaration=True)

    def test_set_xml(self):
        xml = MagicMock()
        path = './xml/element/path'
        key = 'attr-name'
        value_template = MagicMock()
        row = {'a': 1, 'b': 2}
        label = 'label-for-error'
        self.assertEqual(set_xml(xml=xml, path=path, key=key, value_template=value_template, row=row, label=label),
                         True)
        xml.find.assert_called_once_with(path)
        xml.find.return_value.set.assert_called_once_with(key, value_template.format.return_value)
        value_template.format.assert_called_once_with(**row)

    @patch('x4lib.ET')
    def test_set_xml_find_fail(self, patch_ET):
        xml = MagicMock()
        xml.find.return_value = None
        path = './xml/element/path'
        key = 'attr-name'
        value_template = MagicMock()
        row = {'a': 1, 'b': 2}
        label = 'label-for-error'
        with self.assertRaises(SystemExit):
            set_xml(xml=xml, path=path, key=key, value_template=value_template, row=row, label=label)
        xml.find.assert_called_once_with(path)

    def test_set_xml_value_template_error(self):
        xml = MagicMock()
        path = './xml/element/path'
        key = 'attr-name'
        value_template = MagicMock()
        value_template.format.side_effect = Exception
        row = {'a': 1, 'b': 2}
        label = 'label-for-error'
        with self.assertRaises(Exception):
            set_xml(xml=xml, path=path, key=key, value_template=value_template, row=row, label=label)

        xml.find.assert_called_once_with(path)
        value_template.format.assert_called_once_with(**row)


if __name__ == '__main__':
    main()
