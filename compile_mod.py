#!/usr/bin/python3

"""
Compile mods/{mod name}/weapons.xml and mods/{mod name}/ships.xml into mods/{mod name}/* mod files
Use: python3 compile_mod.py {mod name}
"""

import os
import sys
import os.path
import csv
import xml.etree.ElementTree as ET
from copy import deepcopy
from x4lib import get_macros, get_components, get_wares, read_xml, write_xml, set_xml
from constants import MAPPINGS, T_LIST

try:
    import config
except ImportError:
    print('config.py not found, please run setup.sh before using this script!')
    exit(1)


def read_src(filename, src_path=config.SRC, allow_fail=False):
    try:
        filepath = src_path.rstrip('/') + '/' + filename + '.xml'
    except:
        print('read_src fail:', filename, src_path, allow_fail)
        raise
    return read_xml(filepath, allow_fail=allow_fail)


def prep_row(row, page_id, t_id, ware_type, page_ts, **additional_updates):
    _id = row['id']
    row.update(
        macro_id='{ware}_{id}_macro'.format(ware=ware_type, id=_id),
        component_id='{ware}_{id}'.format(ware=ware_type, id=_id),
        page_id=page_id,
    )
    for key, value_template in additional_updates.items():
        row[key] = value_template.format(**row)
    for t_name in T_LIST:
        value = row.get(t_name, '')
        if value:
            row['t_{}_id'.format(t_name)] = t_id
            page_ts.append((t_id, value))
        t_id += 1
    return t_id


def compile_macro(mod, row, obj_path, rel_path, mapping, macro_id='macro_id', base_macro='base_macro'):
    mod_macro_filename = obj_path + row[macro_id] + '.xml'
    src_macro_id = row[base_macro]
    src_macro = read_src(mod.src_macros.get(src_macro_id))
    mod_macro = read_xml(mod_macro_filename, allow_fail=True) or deepcopy(src_macro)
    for path, key, value_template in mapping:
        set_xml(mod_macro, path, key, value_template, row, label='mod_macro')
    write_xml(mod_macro_filename, mod_macro)
    mod.mod_macros.append((row[macro_id],
                           'extensions/{}{}{}'.format(mod.mod_name, rel_path, row[macro_id])))
    return src_macro


def compile_component(mod, row, src_component_id, obj_path, rel_path, mapping):
    mod_component_filename = obj_path + row['component_id'] + '.xml'
    mod_component = (read_xml(mod_component_filename, allow_fail=True) or
                     read_src(mod.src_components.get(src_component_id)))
    for path, key, value_template in mapping:
        set_xml(mod_component, path, key, value_template, row, label='mod_component')
    write_xml(mod_component_filename, mod_component)
    mod.mod_components.append((row['component_id'],
                               'extensions/{}{}{}'.format(mod.mod_name, rel_path, row['component_id'])))


def compile_ware(mod, row):
    ware = mod.old_wares and mod.old_wares.find('./add/ware/component[@ref="{}"]/..'.format(row['macro_id']))
    if ware is None:
        ware = deepcopy(mod.src_wares.find('./ware[@id="{}"]'.format(row['base_macro'][:-6])))
    for path, key, value_template in MAPPINGS['ware']:
        set_xml(ware, path, key, value_template, row, label='mod_macro')
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
    obj_path = mod.mod_path+rel_path
    os.makedirs(obj_path, exist_ok=True)
    reader = csv.DictReader(open(mod.mod_path+'/{}s.csv'.format(ware_type)))
    for row in reader:
        t_id = prep_row(row, page_id, t_id, ware_type, page_ts)
        compile_ware(mod, row)
        src_macro = compile_macro(mod, row, obj_path, rel_path, macro_mappings)
        src_component_id = src_macro.find('./macro/component').get('ref')
        compile_component(mod, row, src_component_id, obj_path, rel_path, component_mappings)

        if additional_compile:
            additional_compile(mod, row, src_macro, obj_path, rel_path)


def compile_weapon_bullet(mod, row, src_macro, obj_path, rel_path):
    row['bullet_macro_id'] = 'bullet_{id}_macro'.format(id=row['id'])
    row['src_bullet_macro_id'] = src_macro.find('./macro/properties/bullet').get('class')
    compile_macro(mod, row, obj_path, rel_path, MAPPINGS['weapon']['bullet_macro'],
                  macro_id='bullet_macro_id', base_macro='src_bullet_macro_id')


def compile_mod(name):
    class mod:
        mod_name = name
        mod_path = config.MODS + '/' + mod_name
        mod_components = []
        mod_macros = []
        mod_ts = {}
        mod_wares = []
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
    args = sys.argv[1:]
    if len(args) < 1:
        print("%s <mod_name>" % sys.argv[0])
    else:
        compile_mod(name=args[0])
