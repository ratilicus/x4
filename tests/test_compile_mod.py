"""
Run tests
Use: ./run_tests.sh
"""

from unittest import TestCase
from unittest.mock import patch, call, MagicMock
import xml.etree.ElementTree as ET
from compile_mod import read_src, prep_row, compile_macro, compile_component, compile_ware, write_index_file, \
    write_ts_file, write_wares_file, compile_ware_type, compile_weapon_bullet, compile_mod


class CompileModUnitTest(TestCase):

    @patch('compile_mod.read_xml')
    def test_read_src(self, patch_read_xml):
        name = 'assets/units/size_s/ship_par_s_scout_01_b_macro'
        src_path = 'path/to/src'
        read_src(name=name, src_path=src_path)
        patch_read_xml.assert_called_once_with('path/to/src/assets/units/size_s/ship_par_s_scout_01_b_macro.xml',
                                               allow_fail=False)

    @patch('compile_mod.read_xml')
    def test_read_src_allow_fail(self, patch_read_xml):
        name = 'assets/units/size_s/ship_par_s_scout_01_b_macro'
        src_path = 'path/to/src'
        read_src(name=name, src_path=src_path, allow_fail=True)
        patch_read_xml.assert_called_once_with('path/to/src/assets/units/size_s/ship_par_s_scout_01_b_macro.xml',
                                               allow_fail=True)

    def test_prep_row(self):
        row = {
            'id': 'pegasus',
            'name': 'Pegasus Xtra',
            'basename': 'Pegasus',
            'variation': 'Xtra',
            'shortvariation': 'X',
        }
        page_id = 1234
        t_id = 10000
        ware_type = 'ship'
        page_ts = []

        self.assertEqual(prep_row(row, page_id, t_id, ware_type, page_ts), t_id+4)

        self.assertEqual(page_ts, [
            (t_id, row['name']),
            (t_id+1, row['basename']),
            (t_id+2, row['variation']),
            (t_id+3, row['shortvariation']),
        ])
        self.assertEqual(row, {
            'id': 'pegasus',
            'name': 'Pegasus Xtra',
            'basename': 'Pegasus',
            'variation': 'Xtra',
            'shortvariation': 'X',

            'component_id': 'ship_pegasus',
            'macro_id': 'ship_pegasus_macro',
            'page_id': 1234,

            't_name_id': t_id,
            't_basename_id': t_id+1,
            't_variation_id': t_id+2,
            't_shortvariation_id': t_id+3,
        })

    @patch('compile_mod.write_xml')
    @patch('compile_mod.update_xml')
    @patch('compile_mod.read_xml')
    @patch('compile_mod.read_src')
    def test_compile_macro(self, patch_read_src, patch_read_xml, patch_update_xml, patch_write_xml):
        mod = MagicMock(mod_name='mod-name')
        mod_path = 'path/to/mod-name/mod/ships/'
        rel_path = '/mod/ships/'
        mapping = MagicMock()
        row = {
            'macro_id': 'some_macro',
            'base_macro': 'some_base_macro'
        }
        mod_xml_filename = 'path/to/mod-name/mod/ships/some_macro.xml'
        src_xml = patch_read_src.return_value
        mod_xml = patch_read_xml.return_value

        self.assertEqual(compile_macro(mod=mod, row=row, mod_path=mod_path, rel_path=rel_path, mapping=mapping),
                         src_xml)
        patch_read_src.assert_called_once_with(mod.src_macros.get.return_value, src_path=mod.src_path)
        patch_read_xml.assert_called_once_with(mod_xml_filename, allow_fail=True)
        patch_update_xml.assert_called_once_with(xml=mod_xml, mapping=mapping, row=row, label='mod_macro')
        patch_write_xml.assert_called_once_with(filename=mod_xml_filename, xml=mod_xml)
        mod.mod_macros.append.assert_called_once_with(('some_macro', 'extensions/mod-name/mod/ships/some_macro'))

    @patch('compile_mod.deepcopy')
    @patch('compile_mod.write_xml')
    @patch('compile_mod.update_xml')
    @patch('compile_mod.read_xml')
    @patch('compile_mod.read_src')
    def test_compile_macro_no_mod_xml(self, patch_read_src, patch_read_xml, patch_update_xml, patch_write_xml,
                                      patch_deepcopy):
        # if no existing xml exists for mod, src xml file is used as template
        mod = MagicMock(mod_name='mod-name')
        mod_path = 'path/to/mod-name/mod/ships/'
        rel_path = '/mod/ships/'
        mapping = MagicMock()
        row = {
            'macro_id': 'some_macro',
            'base_macro': 'some_base_macro'
        }
        mod_xml_filename = 'path/to/mod-name/mod/ships/some_macro.xml'
        patch_read_xml.return_value = None  # pulling existing mod xml, returns nothing in this test, so src should pull
        src_xml = patch_read_src.return_value
        mod_xml = patch_deepcopy.return_value

        self.assertEqual(compile_macro(mod=mod, row=row, mod_path=mod_path, rel_path=rel_path, mapping=mapping),
                         src_xml)
        patch_read_src.assert_called_once_with(mod.src_macros.get.return_value, src_path=mod.src_path)
        patch_read_xml.assert_called_once_with(mod_xml_filename, allow_fail=True)
        patch_deepcopy.assert_called_once_with(src_xml)  # mod_xml = deepcopy(src_xml)
        patch_update_xml.assert_called_once_with(xml=mod_xml, mapping=mapping, row=row, label='mod_macro')
        patch_write_xml.assert_called_once_with(filename=mod_xml_filename, xml=mod_xml)
        mod.mod_macros.append.assert_called_once_with(('some_macro', 'extensions/mod-name/mod/ships/some_macro'))

    @patch('compile_mod.write_xml')
    @patch('compile_mod.update_xml')
    @patch('compile_mod.read_xml')
    @patch('compile_mod.read_src')
    def test_compile_component(self, patch_read_src, patch_read_xml, patch_update_xml, patch_write_xml):
        mod = MagicMock(mod_name='mod-name')
        mod_path = 'path/to/mod-name/mod/ships/'
        rel_path = '/mod/ships/'
        mapping = MagicMock()
        base_component_id = MagicMock()
        row = {
            'component_id': 'some_comp',
        }
        mod_xml_filename = 'path/to/mod-name/mod/ships/some_comp.xml'
        mod_xml = patch_read_xml.return_value

        compile_component(mod=mod, row=row, base_component_id=base_component_id,
                          mod_path=mod_path, rel_path=rel_path, mapping=mapping)

        self.assertEqual(patch_read_src.call_count, 0)
        patch_read_xml.assert_called_once_with(mod_xml_filename, allow_fail=True)
        patch_update_xml.assert_called_once_with(xml=mod_xml, mapping=mapping, row=row, label='mod_component')
        patch_write_xml.assert_called_once_with(filename=mod_xml_filename, xml=mod_xml)
        mod.mod_components.append.assert_called_once_with(('some_comp', 'extensions/mod-name/mod/ships/some_comp'))

    @patch('compile_mod.write_xml')
    @patch('compile_mod.update_xml')
    @patch('compile_mod.read_xml')
    @patch('compile_mod.read_src')
    def test_compile_component_no_mod_xml(self, patch_read_src, patch_read_xml, patch_update_xml, patch_write_xml):
        mod = MagicMock(mod_name='mod-name')
        mod_path = 'path/to/mod-name/mod/ships/'
        rel_path = '/mod/ships/'
        patch_read_xml.return_value = None  # pulling existing mod xml, returns nothing in this test, so src should pull
        mapping = MagicMock()
        base_component_id = MagicMock()
        row = {
            'component_id': 'some_comp',
        }
        mod_xml_filename = 'path/to/mod-name/mod/ships/some_comp.xml'
        src_xml = patch_read_src.return_value

        compile_component(mod=mod, row=row, base_component_id=base_component_id,
                          mod_path=mod_path, rel_path=rel_path, mapping=mapping)

        patch_read_src.assert_called_once_with(mod.src_components.get.return_value, src_path=mod.src_path)
        patch_read_xml.assert_called_once_with(mod_xml_filename, allow_fail=True)
        patch_update_xml.assert_called_once_with(xml=src_xml, mapping=mapping, row=row, label='mod_component')
        patch_write_xml.assert_called_once_with(filename=mod_xml_filename, xml=src_xml)
        mod.mod_components.append.assert_called_once_with(('some_comp', 'extensions/mod-name/mod/ships/some_comp'))

    @patch('compile_mod.write_xml')
    def test_write_ts_file(self, patch_write_xml):
        filename = MagicMock()
        pages = {
            '1001': [
                (10001, 'Pegasus X'),
                (10002, 'Pegasus'),
            ],
            '1002': [
                (10001, 'IRE'),
                (10002, 'PAC'),
            ],
        }
        root = write_ts_file(filename, pages)
        root_str = ET.tostring(root, encoding='unicode')
        self.assertEqual(root_str, '<language id="44">\n<page id="1001">\n<t id="10001">Pegasus X</t>\n<t id="10002">Pegasus</t>\n</page>\n<page id="1002">\n<t id="10001">IRE</t>\n<t id="10002">PAC</t>\n</page>\n</language>\n')