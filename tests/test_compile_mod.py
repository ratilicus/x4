"""
Run tests
Use: ./run_tests.sh
"""

from unittest import TestCase
from unittest.mock import patch, call, MagicMock
import xml.etree.ElementTree as ET
# from compile_mod import read_src, prep_row, compile_macro, compile_component, compile_ware, write_index_file, \
#     write_ts_file, write_wares_file, compile_ware_type, compile_weapon_bullet, compile_mod, MAPPINGS
from compile_mod import X4ModCompiler, MAPPINGS


class ModCompilerUnitTest(TestCase):

    def setUp(self) -> None:
        self.compiler = X4ModCompiler(mod_name='test-mod', config=None)
        self.compiler.mod_path = 'path/to/test-mod'
        self.compiler.src_path = 'path/to/src'
        self.compiler.src_macros = MagicMock()
        self.compiler.src_components = MagicMock()
        self.compiler.src_wares = MagicMock()
        self.compiler.old_wares = MagicMock()
        self.compiler.read_xml = MagicMock()
        self.compiler.write_xml = MagicMock()
        self.compiler.update_xml = MagicMock()
        self.compiler.clone = MagicMock()
        self.compiler.mod_macros = MagicMock()
        self.compiler.mod_components = MagicMock()
        self.compiler.mod_wares = MagicMock()

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

        self.assertEqual(self.compiler.prep_row(row, page_id, t_id, ware_type, page_ts), t_id+4)

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

    def test_write_index_file(self):
        filename = MagicMock()
        entries = [
            ('blah-macro', 'mod/path/to/blah-macro'),
            ('blah-2-macro', 'mod/path/to/blah-2-macro'),
        ]
        root = self.compiler.write_index_file(filename, entries=entries)
        root_str = ET.tostring(root, encoding='unicode')
        self.assertEqual(
            root_str,
            '<diff>\n'
            '<add sel="/index">\n'
            '<entry name="blah-macro" value="mod/path/to/blah-macro" />\n'
            '<entry name="blah-2-macro" value="mod/path/to/blah-2-macro" />\n'
            '</add>\n'
            '</diff>\n'
        )

    def test_write_ts_file(self):
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
        root = self.compiler.write_ts_file(filename, pages=pages)
        root_str = ET.tostring(root, encoding='unicode')
        self.assertEqual(
            root_str,
            '<language id="44">\n'
            '<page id="1001">\n'
            '<t id="10001">Pegasus X</t>\n'
            '<t id="10002">Pegasus</t>\n'
            '</page>\n<page id="1002">\n'
            '<t id="10001">IRE</t>\n'
            '<t id="10002">PAC</t>\n'
            '</page>\n'
            '</language>\n'
        )

    def test_write_wares_file(self):
        filename = MagicMock()
        wares = {
            ET.fromstring('<ware id="some-ware">...</ware>'),
            ET.fromstring('<ware id="some-ware">...</ware>'),
            ET.fromstring('<ware id="some-ware">...</ware>'),
        }
        root = self.compiler.write_wares_file(filename, wares=wares)
        root_str = ET.tostring(root, encoding='unicode')
        self.assertEqual(
            root_str,
            '<diff>\n'
            '<add sel="/wares">\n'
            '<ware id="some-ware">...</ware>'
            '<ware id="some-ware">...</ware>'
            '<ware id="some-ware">...</ware>'
            '</add>\n'
            '</diff>\n'
        )

    def test_read_src(self):
        name = 'assets/units/size_s/ship_par_s_scout_01_b_macro'
        src_path = 'path/to/src'
        self.compiler.read_src(name=name)
        self.compiler.read_xml.assert_called_once_with(
            'path/to/src/assets/units/size_s/ship_par_s_scout_01_b_macro.xml', allow_fail=False)

    def test_compile_connections(self):
        xml = ET.fromstring('<components><component><connections/></component></components>')
        connections = [
            {'connection_name': 'conn_01', 'tags': 'some tags1', 'x': '1.0', 'y': '0.0', 'z': '-2.23', 'qx': '',
             'qy': '', 'qz': '', 'qw': ''},
            {'connection_name': 'conn_02', 'tags': 'some tags2', 'x': '', 'y': '', 'z': '', 'qx': '',
             'qy': '', 'qz': '', 'qw': ''},
            {'connection_name': 'conn_03', 'tags': 'some tags3', 'x': '', 'y': '', 'z': '', 'qx': '1',
             'qy': '2', 'qz': '3', 'qw': '4'},
            {'connection_name': 'conn_04', 'tags': 'some tags4', 'x': '1.1', 'y': '0.2', 'z': '-2.24', 'qx': '9',
             'qy': '8', 'qz': '7', 'qw': '6'},
        ]
        self.compiler.compile_connections(xml, connections)
        self.assertEqual(
            ET.tostring(xml, encoding='unicode'),
            '<components><component><connections>'
            '<connection name="conn_01" tags="some tags1">\n'
            '<offset>\n<position x="1.0" y="0.0" z="-2.23" />\n</offset>\n'
            '</connection>\n'
            '<connection name="conn_02" tags="some tags2">\n<offset>\n</offset>\n</connection>\n'
            '<connection name="conn_03" tags="some tags3">\n'
            '<offset>\n<quaternion qw="4" qx="1" qy="2" qz="3" />\n</offset>\n'
            '</connection>\n'
            '<connection name="conn_04" tags="some tags4">\n'
            '<offset>\n<position x="1.1" y="0.2" z="-2.24" />\n<quaternion qw="6" qx="9" qy="8" qz="7" />\n</offset>\n'
            '</connection>\n'
            '</connections></component></components>')

    def test_read_src_allow_fail(self):
        name = 'assets/units/size_s/ship_par_s_scout_01_b_macro'
        src_path = 'path/to/src'
        self.compiler.read_src(name=name, allow_fail=True)
        self.compiler.read_xml.assert_called_once_with(
            'path/to/src/assets/units/size_s/ship_par_s_scout_01_b_macro.xml', allow_fail=True)

    def test_compile_xml(self):
        self.compiler.read_src = MagicMock()
        src_xml = self.compiler.read_src.return_value
        mod_xml = self.compiler.read_xml.return_value
        mapping = MagicMock()
        row = MagicMock()
        mod_path = 'path/to/modname/mod/type/'
        rel_path = '/mod/type/'
        src_xml_path = 'assets/../some_src_macro'
        mod_id = 'some_mod_macro'
        mod_xml_filename = mod_path + mod_id + '.xml'
        self.assertEqual(
            self.compiler.compile_xml(row=row, mod_path=mod_path, rel_path=rel_path, src_xml_path=src_xml_path,
                                      mapping=mapping, mod_id=mod_id),
            (src_xml, (mod_id, 'extensions/{}{}{}'.format(self.compiler.mod_name, rel_path, mod_id)))
        )
        self.compiler.read_src.assert_called_once_with(src_xml_path)
        self.compiler.read_xml.assert_called_once_with(mod_xml_filename, allow_fail=True)
        self.compiler.update_xml.assert_called_once_with(xml=mod_xml, mapping=mapping, row=row,
                                                         label='compile_xml:' + mod_id)
        self.compiler.write_xml.assert_called_once_with(filename=mod_xml_filename, xml=mod_xml)

    def test_compile_xml_no_mod_xml(self):
        self.compiler.read_src = MagicMock()
        src_xml = self.compiler.read_src.return_value
        self.compiler.read_xml.return_value = None
        src_clone_xml = self.compiler.clone.return_value
        mapping = MagicMock()
        row = MagicMock()
        mod_path = 'path/to/modname/mod/type/'
        rel_path = '/mod/type/'
        src_xml_path = 'assets/../some_src_macro'
        mod_id = 'some_mod_macro'
        mod_xml_filename = mod_path + mod_id + '.xml'
        self.assertEqual(
            self.compiler.compile_xml(row=row, mod_path=mod_path, rel_path=rel_path, src_xml_path=src_xml_path,
                                      mapping=mapping, mod_id=mod_id),
            (src_xml, (mod_id, 'extensions/{}{}{}'.format(self.compiler.mod_name, rel_path, mod_id)))
        )
        self.compiler.read_src.assert_called_once_with(src_xml_path)
        self.compiler.read_xml.assert_called_once_with(mod_xml_filename, allow_fail=True)
        self.compiler.clone.assert_called_once_with(src_xml)
        self.compiler.update_xml.assert_called_once_with(xml=src_clone_xml, mapping=mapping, row=row,
                                                         label='compile_xml:' + mod_id)
        self.compiler.write_xml.assert_called_once_with(filename=mod_xml_filename, xml=src_clone_xml)

    def test_compile_macro(self):
        self.compiler.compile_xml = MagicMock()
        src_xml, mod_data = self.compiler.compile_xml.return_value = (MagicMock(), MagicMock())
        mod_path = 'path/to/mod-name/mod/ships/'
        rel_path = '/mod/ships/'
        src_xml_path = 'src/path/to/some_base_macro'
        mapping = MagicMock()
        row = {
            'macro_id': 'some_macro',
            'base_macro': 'some_base_macro'
        }
        self.compiler.src_macros = {'some_base_macro': src_xml_path}
        self.assertEqual(self.compiler.compile_macro(row=row, mod_path=mod_path, rel_path=rel_path, mapping=mapping),
                         src_xml)
        self.compiler.compile_xml.assert_called_once_with(row=row, mod_path=mod_path, rel_path=rel_path,
                                                          src_xml_path=src_xml_path, mapping=mapping,
                                                          mod_id='some_macro')
        self.compiler.mod_macros.append.assert_called_once_with(mod_data)

    def test_compile_macro_alt_keys(self):
        # when processing sub object macros, you might have to override the macro id and base
        # (eg. for weapons you have the main weapon macro and base, but also need to mod bullet macro(
        self.compiler.compile_xml = MagicMock()
        src_xml, mod_data = self.compiler.compile_xml.return_value = (MagicMock(), MagicMock())
        mod_path = 'path/to/mod-name/mod/ships/'
        rel_path = '/mod/ships/'
        src_xml_path = 'src/path/to/some_base_macro'
        mapping = MagicMock()
        row = {
            'macro_id': 'some_macro',
            'base_macro': 'some_base_macro',
            'other_macro_id': 'some_other_macro',
            'other_base_macro_id': 'some_other_base_macro',
        }
        self.compiler.src_macros = {'some_other_base_macro': src_xml_path}
        self.assertEqual(self.compiler.compile_macro(row=row, mod_path=mod_path, rel_path=rel_path, mapping=mapping,
                                                     id_key='other_macro_id', base_key='other_base_macro_id'),
                         src_xml)
        self.compiler.compile_xml.assert_called_once_with(row=row, mod_path=mod_path, rel_path=rel_path,
                                                          src_xml_path=src_xml_path, mapping=mapping,
                                                          mod_id='some_other_macro')
        self.compiler.mod_macros.append.assert_called_once_with(mod_data)

    def test_compile_component(self):
        self.compiler.compile_xml = MagicMock()
        src_xml, mod_data = self.compiler.compile_xml.return_value = (MagicMock(), MagicMock())
        mod_path = 'path/to/mod-name/mod/ships/'
        rel_path = '/mod/ships/'
        src_xml_path = 'src/path/to/some_base_comp'
        mapping = MagicMock()
        connections = MagicMock()
        row = {
            'component_id': 'some_comp',
        }
        base_component_id = 'src_some_comp'
        self.compiler.src_components = {base_component_id: src_xml_path}
        self.assertEqual(
            self.compiler.compile_component(row=row, base_component_id=base_component_id,
                                            mod_path=mod_path, rel_path=rel_path, mapping=mapping,
                                            connections=connections),
            src_xml)
        self.compiler.compile_xml.assert_called_once_with(row=row, mod_path=mod_path, rel_path=rel_path,
                                                          src_xml_path=src_xml_path, mapping=mapping,
                                                          mod_id='some_comp', connections=connections)
        self.compiler.mod_components.append.assert_called_once_with(mod_data)

    def test_compile_ware(self):
        row = {
            'macro_id': 'some_macro',
            'base_macro': 'some_base_macro',
            'factions': 'a b'
        }
        ware = self.compiler.old_wares.find.return_value = ET.fromstring('<ware><owner faction="c" /></ware>')
        self.compiler.compile_ware(row)
        self.compiler.old_wares.find.assert_called_once_with('./add/ware/component[@ref="some_macro"]/..')
        self.compiler.update_xml.assert_called_once_with(xml=ware, mapping=self.compiler.WARE_MAPPINGS['ware'],
                                                         row=row, label='mod_ware')
        self.compiler.mod_wares.append.assert_called_once_with(ware)
        self.assertEqual(
            ET.tostring(ware),
            b'<ware><owner faction="a" /><owner faction="b" /></ware>')

    def test_compile_ware_no_mod_ware(self):
        # when there is no existing mod ware, use the one from base/src macro
        row = {
            'macro_id': 'some_macro',
            'base_macro': 'some_base_macro',
        }
        self.compiler.old_wares = None
        self.compiler.compile_ware(row)
        ware = self.compiler.clone.return_value
        self.compiler.clone.assert_called_once_with(self.compiler.src_wares.find.return_value)
        self.compiler.src_wares.find.assert_called_once_with('./ware/component[@ref="some_base_macro"]/..')
        self.compiler.update_xml.assert_called_once_with(xml=ware, mapping=MAPPINGS['ware'], row=row, label='mod_ware')
        self.compiler.mod_wares.append.assert_called_once_with(ware)

    def test_ware_type_connections(self):
        ware_type = 'some-ware-type'
        conn = [
            {'id': 'ship1', 'connection_name': 'c1'},
            {'id': 'ship1', 'connection_name': 'c2'},
            {'id': 'ship2', 'connection_name': 'c3'},
        ]
        self.compiler.csv_data = {
            ware_type+'.conn': conn
        }
        self.assertEqual(self.compiler.get_ware_type_connections(ware_type), {
            'ship1': conn[0:2],
            'ship2': conn[2:3],
        })

    def test_compile_ware_type(self):
        ware_type = 'shield'
        rows = [
            MagicMock(), MagicMock()
        ]
        self.compiler.csv_data = {ware_type: rows}
        self.compiler.prep_row = MagicMock(return_value=100010)
        self.compiler.compile_ware = MagicMock()
        self.compiler.compile_macro = MagicMock()
        src_macros = self.compiler.compile_macro.side_effect = [MagicMock(), MagicMock()]
        self.compiler.compile_component = MagicMock()

        page_id = 10001
        self.compiler.compile_ware_type(ware_type=ware_type, page_id=page_id)
        self.assertEqual(self.compiler.mod_ts, {page_id: []})
        self.compiler.prep_row.assert_has_calls([
            call(rows[0], page_id, 100000, ware_type, [], has_ts=True),
            call(rows[1], page_id, 100010, ware_type, [], has_ts=True),
        ])
        self.compiler.compile_ware.assert_has_calls([
            call(rows[0]),
            call(rows[1]),
        ])
        mod_path = self.compiler.mod_path+'/mod/{}s/'.format(ware_type)
        rel_path = '/mod/{}s/'.format(ware_type)

        macro_mapping = self.compiler.WARE_MAPPINGS[ware_type]['macro']
        component_mapping = self.compiler.WARE_MAPPINGS[ware_type]['component']

        self.compiler.compile_macro.assert_has_calls([
            call(row=rows[0], mod_path=mod_path, rel_path=rel_path, mapping=macro_mapping),
            call(row=rows[1], mod_path=mod_path, rel_path=rel_path, mapping=macro_mapping),
        ])
        self.compiler.compile_component.assert_has_calls([
            call(row=rows[0], mod_path=mod_path, rel_path=rel_path, mapping=component_mapping,
                 base_component_id=src_macros[0].find.return_value.get.return_value, connections=[]),
            call(row=rows[1], mod_path=mod_path, rel_path=rel_path, mapping=component_mapping,
                 base_component_id=src_macros[1].find.return_value.get.return_value, connections=[]),
        ])
        src_macros[0].find.assert_called_once_with('./macro/component')
        src_macros[0].find.return_value.get.assert_called_once_with('ref')
        src_macros[1].find.assert_called_once_with('./macro/component')
        src_macros[1].find.return_value.get.assert_called_once_with('ref')

    def test_compile(self):
        self.compiler.mod_ts = MagicMock()
        self.compiler.compile_ware_type = MagicMock()
        self.compiler.write_index_file = MagicMock()
        self.compiler.write_ts_file = MagicMock()
        self.compiler.write_wares_file = MagicMock()

        self.compiler.compile()

        self.compiler.compile_ware_type.assert_has_calls([
            call(ware_type='bullet', page_id=20105, has_ts=False, has_ware=False),
            call(ware_type='weapon', page_id=20105),
            call(ware_type='shield', page_id=20106),
            call(ware_type='ship', page_id=20101),
        ])

        self.compiler.write_index_file.assert_has_calls([
            call(self.compiler.mod_path+'/index/macros.xml', self.compiler.mod_macros),
            call(self.compiler.mod_path+'/index/components.xml', self.compiler.mod_components),
        ])
        self.compiler.write_ts_file.assert_called_once_with(
            self.compiler.mod_path+'/t/0001-L044.xml', self.compiler.mod_ts)
        self.compiler.write_wares_file.assert_called_once_with(
            self.compiler.mod_path+'/libraries/wares.xml', self.compiler.mod_wares)

    @patch('compile_mod.glob')
    def test_read_mod_csv_data(self, patch_glob):
        patch_glob.glob.return_value = [
            'path/to/file3.csv',
            'path/to/file1.csv',
            'path/to/file2.csv',
        ]
        self.compiler.read_csv = MagicMock()
        self.compiler.read_mod_csv_data()
        self.compiler.read_csv.assert_has_calls([
            call('path/to/file1.csv', self.compiler.csv_data),
            call('path/to/file2.csv', self.compiler.csv_data),
            call('path/to/file3.csv', self.compiler.csv_data),
        ])
        patch_glob.glob.assert_called_once_with('path/to/test-mod/*.csv')

    @patch('compile_mod.X4ModCompiler.get_wares')
    @patch('compile_mod.X4ModCompiler.get_components')
    @patch('compile_mod.X4ModCompiler.get_macros')
    def test_init(self, patch_get_macros, patch_get_components, patch_get_wares):
        src_wares, old_wares = patch_get_wares.side_effect = [MagicMock(), MagicMock()]
        mod_name = 'my-mod-name'
        config = MagicMock(MODS='path/to/mods')
        mod_path = config.MODS + '/' + mod_name
        compiler = X4ModCompiler(mod_name=mod_name, config=config)
        patch_get_macros.assert_called_once_with(src_path=config.SRC)
        patch_get_components.assert_called_once_with(src_path=config.SRC)
        patch_get_wares.assert_has_calls([
            call(src_path=config.SRC),
            call(src_path=mod_path, allow_fail=True),
        ])
        self.assertEqual(compiler.mod_name, mod_name)
        self.assertEqual(compiler.mod_components, [])
        self.assertEqual(compiler.mod_macros, [])
        self.assertEqual(compiler.mod_ts, {})
        self.assertEqual(compiler.mod_wares, [])
        self.assertEqual(compiler.mod_path, mod_path)
        self.assertEqual(compiler.src_path, config.SRC)
        self.assertEqual(compiler.src_macros, patch_get_macros.return_value)
        self.assertEqual(compiler.src_components, patch_get_components.return_value)
        self.assertEqual(compiler.src_wares, src_wares)
        self.assertEqual(compiler.old_wares, old_wares)






