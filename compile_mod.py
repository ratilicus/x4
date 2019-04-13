#!/usr/bin/python3

"""
Compile mods/{mod name}/weapons.xml and mods/{mod name}/ships.xml into mods/{mod name}/* mod files
Use: python3 compile_mod.py {mod name}
"""

import os
import sys
import os.path
import csv
import logging
import xml.etree.ElementTree as ET
from copy import deepcopy
from constants import MAPPINGS, T_LIST
from x4lib import get_config, get_macros, get_components, get_wares, read_xml, write_xml, update_xml

logger = logging.getLogger('x4.' + __name__)


def read_src(name, src_path, allow_fail=False):
    filepath = src_path.rstrip('/') + '/' + name + '.xml'
    return read_xml(filepath, allow_fail=allow_fail)


def prep_row(row, page_id, t_id, ware_type, page_ts):
    _id = row['id']
    row.update(
        macro_id='{ware}_{id}_macro'.format(ware=ware_type, id=_id),
        component_id='{ware}_{id}'.format(ware=ware_type, id=_id),
        page_id=page_id,
    )
    for t_name in T_LIST:
        value = row.get(t_name, '')
        if value:
            row['t_{}_id'.format(t_name)] = t_id
            page_ts.append((t_id, value))
            t_id += 1
    return t_id


def compile_macro(mod, row, mod_path, rel_path, mapping, macro_id='macro_id', base_macro='base_macro'):
    mod_xml_filename = mod_path + row[macro_id] + '.xml'
    src_xml_id = row[base_macro]
    src_xml = read_src(mod.src_macros.get(src_xml_id), src_path=mod.src_path)
    mod_xml = read_xml(mod_xml_filename, allow_fail=True) or deepcopy(src_xml)
    update_xml(xml=mod_xml, mapping=mapping, row=row, label='mod_macro')
    write_xml(filename=mod_xml_filename, xml=mod_xml)
    mod.mod_macros.append((row[macro_id],
                           'extensions/{}{}{}'.format(mod.mod_name, rel_path, row[macro_id])))
    return src_xml


def compile_component(mod, row, base_component_id, mod_path, rel_path, mapping):
    mod_xml_filename = mod_path + row['component_id'] + '.xml'
    mod_xml = (read_xml(mod_xml_filename, allow_fail=True) or
               read_src(mod.src_components.get(base_component_id), src_path=mod.src_path))
    update_xml(xml=mod_xml, mapping=mapping, row=row, label='mod_component')
    write_xml(filename=mod_xml_filename, xml=mod_xml)
    mod.mod_components.append((row['component_id'],
                               'extensions/{}{}{}'.format(mod.mod_name, rel_path, row['component_id'])))


def compile_ware(mod, row):
    ware = mod.old_wares and mod.old_wares.find('./add/ware/component[@ref="{}"]/..'.format(row['macro_id']))
    if ware is None:
        ware = deepcopy(mod.src_wares.find('./ware[@id="{}"]'.format(row['base_macro'][:-6])))
    update_xml(xml=ware, mapping=MAPPINGS['ware'], row=row, label='mod_ware')
    mod.mod_wares.append(ware)


def write_index_file(filename, entries):
    diff = ET.Element('diff')
    diff.text = '\n'
    diff.tail = '\n'
    add = ET.Element('add', sel='/index')
    add.text = '\n'
    add.tail = '\n'
    diff.append(add)
    for name, value in entries:
        entry = ET.Element('entry', name=name, value=value)
        entry.tail = '\n'
        add.append(entry)
    write_xml(filename, ET.ElementTree(diff))


def write_ts_file(filename, pages):
    lang = ET.Element('language', id="44")
    lang.text = '\n'
    lang.tail = '\n'
    for page_id, ts in pages.items():
        page = ET.Element('page', id='{}'.format(page_id))
        page.text = '\n'
        page.tail = '\n'
        lang.append(page)
        for t_id, value in ts:
            t = ET.Element('t', id='{}'.format(t_id))
            t.text = value
            t.tail = '\n'
            page.append(t)
    write_xml(filename, ET.ElementTree(lang))
    return lang


def write_wares_file(filename, wares):
    diff = ET.Element('diff')
    diff.text = '\n'
    diff.tail = '\n'
    add = ET.Element('add', sel='/wares')
    add.text = '\n'
    add.tail = '\n'
    diff.append(add)
    for ware in wares:
        add.append(ware)
    write_xml(filename, ET.ElementTree(diff))


def compile_ware_type(mod, ware_type, page_id, t_id=100000, additional_compile=None):
    rel_path = '/mod/{}s/'.format(ware_type)
    macro_mappings = MAPPINGS[ware_type]['macro']
    component_mappings = MAPPINGS[ware_type]['component']
    page_ts = []
    mod.mod_ts[page_id] = page_ts
    mod_path = mod.mod_path+rel_path
    os.makedirs(mod_path, exist_ok=True)
    reader = csv.DictReader(open(mod.mod_path+'/{}s.csv'.format(ware_type)))
    for row in reader:
        t_id = prep_row(row, page_id, t_id, ware_type, page_ts)
        compile_ware(mod, row)
        src_macro = compile_macro(mod, row, mod_path, rel_path, macro_mappings)
        base_component_id = src_macro.find('./macro/component').get('ref')
        compile_component(mod, row, base_component_id, mod_path, rel_path, component_mappings)

        if additional_compile:
            additional_compile(mod, row, src_macro, mod_path, rel_path)


def compile_weapon_bullet(mod, row, src_macro, mod_path, rel_path):
    row['bullet_macro_id'] = 'bullet_{id}_macro'.format(id=row['id'])
    row['src_bullet_macro_id'] = src_macro.find('./macro/properties/bullet').get('class')
    compile_macro(mod, row, mod_path, rel_path, MAPPINGS['weapon']['bullet_macro'],
                  macro_id='bullet_macro_id', base_macro='src_bullet_macro_id')


def compile_mod(name, config):
    class mod:
        mod_name = name
        mod_path = config.MODS + '/' + mod_name
        mod_components = []
        mod_macros = []
        mod_ts = {}
        mod_wares = []
        src_path=config.SRC
        src_macros = get_macros(src_path=config.SRC)
        src_components = get_components(src_path=config.SRC)
        src_wares = get_wares(src_path=config.SRC)
        old_wares = get_wares(src_path=mod_path, allow_fail=True)

    compile_ware_type(mod, ware_type='weapon', page_id=20105, additional_compile=compile_weapon_bullet)
    compile_ware_type(mod, ware_type='shield', page_id=20106)
    compile_ware_type(mod, ware_type='ship', page_id=20101)

    os.makedirs(mod.mod_path+'/index/', exist_ok=True)
    write_index_file(mod.mod_path+'/index/macros.xml', mod.mod_macros)
    write_index_file(mod.mod_path+'/index/components.xml', mod.mod_components)

    os.makedirs(mod.mod_path+'/t/', exist_ok=True)
    write_ts_file(mod.mod_path+'/t/0001-L044.xml', mod.mod_ts)

    os.makedirs(mod.mod_path+'/libraries/', exist_ok=True)
    write_wares_file(mod.mod_path+'/libraries/wares.xml', mod.mod_wares)


if __name__ == '__main__':
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)

    args = sys.argv[1:]
    if len(args) < 1:
        logger.info("%s <mod_name>", sys.argv[0])
    else:
        compile_mod(name=args[0], config=get_config())
