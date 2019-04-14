#!/usr/bin/python3

"""
Compile mods/{mod name}/weapons.xml and mods/{mod name}/ships.xml into mods/{mod name}/* mod files
Use: python3 compile_mod.py {mod name}
"""

import sys
import csv
import logging
from copy import deepcopy
import xml.etree.ElementTree as ET
from constants import MAPPINGS, T_LIST
from x4lib import get_config, ModUtilMixin

logger = logging.getLogger('x4.' + __name__)


class X4ModCompiler(ModUtilMixin):
    WARE_MAPPINGS = MAPPINGS
    T_NAMES_LIST = T_LIST

    def prep_row(self, row, page_id, t_id, ware_type, page_ts):
        _id = row['id']
        row.update(
            macro_id='{ware}_{id}_macro'.format(ware=ware_type, id=_id),
            component_id='{ware}_{id}'.format(ware=ware_type, id=_id),
            page_id=page_id,
        )
        for t_name in self.T_NAMES_LIST:
            value = row.get(t_name, '')
            if value:
                row['t_{}_id'.format(t_name)] = t_id
                page_ts.append((t_id, value))
                t_id += 1
        return t_id

    def write_index_file(self, filename, entries):
        root = ET.Element('diff')
        root.text = root.tail = '\n'
        add = ET.Element('add', sel='/index')
        add.text = add.tail = '\n'
        root.append(add)
        for name, value in entries:
            entry = ET.Element('entry', name=name, value=value)
            entry.tail = '\n'
            add.append(entry)
        self.write_xml(filename, ET.ElementTree(root))
        return root

    def write_ts_file(self, filename, pages):
        root = ET.Element('language', id="44")
        root.text = root.tail = '\n'
        for page_id, ts in pages.items():
            page = ET.Element('page', id='{}'.format(page_id))
            page.text = page.tail = '\n'
            root.append(page)
            for t_id, value in ts:
                t = ET.Element('t', id='{}'.format(t_id))
                t.text = value
                t.tail = '\n'
                page.append(t)
        self.write_xml(filename, ET.ElementTree(root))
        return root

    def write_wares_file(self, filename, wares):
        root = ET.Element('diff')
        root.text = root.tail = '\n'
        add = ET.Element('add', sel='/wares')
        add.text = add.tail = '\n'
        root.append(add)
        for ware in wares:
            add.append(ware)
        self.write_xml(filename, ET.ElementTree(root))
        return root

    def csv_data(self, ware_type):
        return csv.DictReader(open(self.mod_path+'/{}s.csv'.format(ware_type)))

    def read_src(self, name, allow_fail=False):
        filepath = self.src_path.rstrip('/') + '/' + name + '.xml'
        return self.read_xml(filepath, allow_fail=allow_fail)

    def compile_xml(self, row, mod_path, rel_path, src_xml_path, mapping, mod_id):
        """
        This tries to pull existing mod xml and update values from row data,
        if no mod xml exists, use src xml.
        (this allows existing mod to have additional changes that will not be lost if this is re-run)
        :param row: (dict) row data from csv
        :param mod_path: (str) abs path to mod
        :param rel_path: (str) rel path in mod (after mod-name)
        :param src_xml_path: (str) rel path in src dir to src xml
        :param mapping: (list) list of xml keys to change
        :param mod_id: (list) id from csv row
        :return:
        """
        label = 'compile_xml:' + mod_id
        mod_xml_filename = mod_path + mod_id + '.xml'
        src_xml = self.read_src(src_xml_path)
        mod_xml = self.read_xml(mod_xml_filename, allow_fail=True)
        if mod_xml is None:
            # if there is no existing mod version of the xml, use a copy of the source xml
            mod_xml = self.clone(src_xml)
        self.update_xml(xml=mod_xml, mapping=mapping, row=row, label=label)
        self.write_xml(filename=mod_xml_filename, xml=mod_xml)
        return src_xml, (mod_id, 'extensions/{}{}{}'.format(self.mod_name, rel_path, mod_id))

    def compile_macro(self, row, mod_path, rel_path, mapping, id_key='macro_id', base_key='base_macro'):
        """
        Compile macro (takes mod macro, or src macro and updates data from csv
        id_key, base_key can be used when dealing with multiple macros, such as in weapons, where
        we update both weapon macro, and bullet macro
        :param row: (dict) row data from csv
        :param mod_path: (str) abs path to mod
        :param rel_path: (str) rel path in mod (after mod-name)
        :param mapping: (list) list of xml keys to change
        :param id_key: key to id field in row
        :param base_key: key to base/src id in row
        :return:
        """
        mod_id = row[id_key]
        src_xml_path = self.src_macros[row[base_key]]
        src_xml, mod_data = self.compile_xml(row=row, mod_path=mod_path, rel_path=rel_path,
                                             src_xml_path=src_xml_path, mapping=mapping, mod_id=mod_id)
        self.mod_macros.append(mod_data)
        return src_xml

    def compile_component(self, row, base_component_id, mod_path, rel_path, mapping):
        """
        Compile component (takes mod component or src component and updates data from csv
        :param row: (dict) row data from csv
        :param base_component_id: (str) id of src component
        :param mod_path: (str) abs path to mod
        :param rel_path: (str) rel path in mod (after mod-name)
        :param mapping: (list) list of xml keys to change
        :return:
        """
        mod_id = row['component_id']
        src_xml_path = self.src_components[base_component_id]
        src_xml, mod_data = self.compile_xml(row=row, mod_path=mod_path, rel_path=rel_path,
                                             src_xml_path=src_xml_path, mapping=mapping, mod_id=mod_id)
        self.mod_components.append(mod_data)
        return src_xml

    def compile_ware(self, row):
        """
        This tries to pull existing ware xml data and update values from row data,
        if no mod xml data exists, use src xml.
        (this allows existing mod to have additional changes that will not be lost if this is re-run)
        :param row: (dict) row data from csv
        :return:
        """
        ware = self.old_wares and self.old_wares.find('./add/ware/component[@ref="{}"]/..'.format(row['macro_id']))
        if ware is None:
            ware = self.clone(self.src_wares.find('./ware/component[@ref="{}"]/..'.format(row['base_macro'])))
        self.update_xml(xml=ware, mapping=self.WARE_MAPPINGS['ware'], row=row, label='mod_ware')
        self.mod_wares.append(ware)

    def compile_ware_type(self, ware_type, page_id, t_id=100000, additional_compile=None):
        rel_path = '/mod/{}s/'.format(ware_type)
        macro_mapping = self.WARE_MAPPINGS[ware_type]['macro']
        component_mapping = self.WARE_MAPPINGS[ware_type]['component']
        page_ts = []
        self.mod_ts[page_id] = page_ts
        mod_path = self.mod_path+rel_path
        reader = self.csv_data(ware_type)
        for row in reader:
            t_id = self.prep_row(row, page_id, t_id, ware_type, page_ts)
            self.compile_ware(row)
            src_macro = self.compile_macro(row=row, mod_path=mod_path, rel_path=rel_path, mapping=macro_mapping)
            base_component_id = src_macro.find('./macro/component').get('ref')
            self.compile_component(row=row, base_component_id=base_component_id, mod_path=mod_path, rel_path=rel_path,
                                   mapping=component_mapping)

            if additional_compile is not None:
                additional_compile(row=row, src_macro=src_macro, mod_path=mod_path, rel_path=rel_path)

    def compile_weapon_bullet(self, row, src_macro, mod_path, rel_path):
        # additional compile function for bullet macro compiling
        row['bullet_macro_id'] = 'bullet_{id}_macro'.format(id=row['id'])
        row['src_bullet_macro_id'] = src_macro.find('./macro/properties/bullet').get('class')
        self.compile_macro(row=row, mod_path=mod_path, rel_path=rel_path,
                           mapping=self.WARE_MAPPINGS['weapon']['bullet_macro'],
                           id_key='bullet_macro_id', base_key='src_bullet_macro_id')

    def compile(self):
        self.compile_ware_type(ware_type='weapon', page_id=20105, additional_compile=self.compile_weapon_bullet)
        self.compile_ware_type(ware_type='shield', page_id=20106)
        self.compile_ware_type(ware_type='ship', page_id=20101)

        self.write_index_file(self.mod_path+'/index/macros.xml', self.mod_macros)
        self.write_index_file(self.mod_path+'/index/components.xml', self.mod_components)
        self.write_ts_file(self.mod_path+'/t/0001-L044.xml', self.mod_ts)
        self.write_wares_file(self.mod_path+'/libraries/wares.xml', self.mod_wares)

    def __init__(self, name, config):
        self.mod_name = name
        self.mod_macros = []
        self.mod_components = []
        self.mod_ts = {}
        self.mod_wares = []
        if config:
            self.mod_path = config.MODS + '/' + self.mod_name
            self.src_path = config.SRC
            self.src_macros = self.get_macros(src_path=config.SRC)
            self.src_components = self.get_components(src_path=config.SRC)
            self.src_wares = self.get_wares(src_path=config.SRC)
            self.old_wares = self.get_wares(src_path=self.mod_path, allow_fail=True)


if __name__ == '__main__':
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)

    args = sys.argv[1:]
    if len(args) < 1:
        logger.info("%s <mod_name>", sys.argv[0])
    else:
        compiler = X4ModCompiler(name=args[0], config=get_config())
        compiler.compile()
