#!/usr/bin/python3

import os
import sys
import os.path
import csv
import xml.etree.ElementTree as ET
from x4lib import get_macros, get_components, get_wares, read_xml, write_xml, set_xml

"""
Compile mods/{mod name}/weapons.xml and mods/{mod name}/ships.xml into mods/{mod name}/* mod files
Use: python3 compile_mod.py {mod name}
"""

try:
    import config
except ImportError:
    print('config.py not found, please run setup.sh before using this script!')
    exit(1)


WEAPON_COMPONENT_MAPPINGS = [
    ('./component', 'name', '{weapon_component_id}'),
    ('./component/connections/connection[@name="WeaponCon_01"]', 'tags', '{tags}'),
]
WEAPON_MACRO_MAPPINGS = [
    ('./macro', 'name', '{weapon_macro_id}'),
    ('./macro/component', 'ref', '{weapon_component_id}'),
    ('./macro/properties/identification', 'name', '{{{page_id}, {t_name_id}}}'),
    ('./macro/properties/identification', 'basename', '{{{page_id}, {t_basename_id}}}'),
    ('./macro/properties/identification', 'shortname', '{{{page_id}, {t_shortname_id}}}'),
    ('./macro/properties/identification', 'description', '{{{page_id}, {t_description_id}}}'),
    ('./macro/properties/identification', 'mk', '{mk}'),
    ('./macro/properties/bullet', 'class', '{bullet_macro_id}'),
    ('./macro/properties/heat', 'overheat', '{overheat}'),
    ('./macro/properties/heat', 'cooldelay', '{cooldelay}'),
    ('./macro/properties/heat', 'coolrate', '{coolrate}'),
    ('./macro/properties/heat', 'reenable', '{reenable}'),
    ('./macro/properties/rotationspeed', 'max', '{rotation_spd}'),
    ('./macro/properties/rotationacceleration', 'max', '{rotation_acc}'),
    ('./macro/properties/hull', 'max', '{hull}'),
]
BULLET_MACRO_MAPPINGS = [
    ('./macro', 'name', '{bullet_macro_id}'),
    ('./macro/properties/bullet', 'speed', '{bullet_speed}'),
    ('./macro/properties/bullet', 'lifetime', '{bullet_lifetime}'),
    ('./macro/properties/bullet', 'heat', '{bullet_heat}'),
    ('./macro/properties/bullet', 'reload', '{bullet_reload}'),
    ('./macro/properties/bullet', 'damage', '{bullet_damage}'),
    ('./macro/properties/bullet', 'shield', '{bullet_shield}'),
    ('./macro/properties/bullet', 'repair', '{bullet_repair}'),
]
WARE_MAPPINGS = [
    ('.', 'id', '{ware_component_id}'),
    ('.', 'name', '{{{page_id}, {t_name_id}}}'),
    ('.', 'description', '{{{page_id}, {t_description_id}}}'),
    ('./price', 'min', '{price_min}'),
    ('./price', 'average', '{price_avg}'),
    ('./price', 'max', '{price_max}'),
    ('./component', 'ref', '{ware_macro_id}'),
    ('./restriction', 'licence', '{restriction}'),
]
SHIP_COMPONENT_MAPPINGS = [
    ('./component', 'name', '{ship_component_id}'),
]
SHIP_MACRO_MAPPINGS = [
    ('./macro', 'name', '{ship_macro_id}'),
    ('./macro/component', 'ref', '{ship_component_id}'),
    ('./macro/properties/identification', 'name', '{{{page_id}, {t_name_id}}}'),
    ('./macro/properties/identification', 'basename', '{{{page_id}, {t_basename_id}}}'),
    ('./macro/properties/identification', 'description', '{{{page_id}, {t_description_id}}}'),
    ('./macro/properties/identification', 'variation', '{{{page_id}, {t_variation_id}}}'),
    ('./macro/properties/identification', 'shortvariation', '{{{page_id}, {t_short_variation_id}}}'),
    ('./macro/properties/hull', 'max', '{hull}'),
    ('./macro/properties/people', 'capacity', '{people}'),
    ('./macro/properties/physics', 'mass', '{mass}'),
    ('./macro/properties/physics/inertia', 'pitch', '{inertia_pitch}'),
    ('./macro/properties/physics/inertia', 'yaw', '{inertia_yaw}'),
    ('./macro/properties/physics/inertia', 'roll', '{inertia_roll}'),
    ('./macro/properties/physics/drag', 'forward', '{drag_forward}'),
    ('./macro/properties/physics/drag', 'reverse', '{drag_reverse}'),
    ('./macro/properties/physics/drag', 'horizontal', '{drag_horizontal}'),
    ('./macro/properties/physics/drag', 'vertical', '{drag_vertical}'),
    ('./macro/properties/physics/drag', 'pitch', '{drag_pitch}'),
    ('./macro/properties/physics/drag', 'yaw', '{drag_yaw}'),
    ('./macro/properties/physics/drag', 'roll', '{drag_roll}'),
]


def read_src(filename, src_path=config.SRC, allow_fail=False):
    filepath = src_path.rstrip('/') + '/' + filename + '.xml'
    return read_xml(filepath, allow_fail=allow_fail)


def compile_weapons(mod, rel_path='/mod/weapons/'):
    page_id = 20105
    t_id = 10000
    page_ts = []
    mod.mod_ts[page_id] = page_ts
    weapon_path = mod.mod_path+rel_path
    os.makedirs(weapon_path, exist_ok=True)

    reader = csv.DictReader(open(mod.mod_path+'/weapons.csv'))
    for row in reader:
        _id = row['id']
        row.update(
            weapon_macro_id='weapon_{id}_macro'.format(**row),
            weapon_component_id='weapon_{id}'.format(**row),
            ware_macro_id='weapon_{id}_macro'.format(**row),
            ware_component_id='weapon_{id}'.format(**row),
            bullet_macro_id='bullet_{id}_macro'.format(**row),
            page_id=page_id, t_name_id=t_id, t_basename_id=t_id+1, t_shortname_id=t_id+2, 
            t_description_id=t_id+3)
        page_ts.append((row['t_name_id'], row['name']))
        page_ts.append((row['t_basename_id'], row['basename']))
        page_ts.append((row['t_shortname_id'], row['shortname']))
        page_ts.append((row['t_description_id'], row['description']))
        t_id += 10

        out_weapon_component_filename = weapon_path+row['weapon_component_id']+'.xml'
        out_weapon_macro_filename = weapon_path+row['weapon_macro_id']+'.xml'
        out_bullet_macro_filename = weapon_path+row['bullet_macro_id']+'.xml'

        # read weapon macro (try existing mod file first, in case it has other modifications)
        weapon_macro_id = row['base_weapon_macro']
        src_weapon_macro = read_src(mod.src_macros.get(weapon_macro_id))
        weapon_macro = read_xml(out_weapon_macro_filename, allow_fail=True) or src_weapon_macro
        weapon_component_id = src_weapon_macro.find('./macro/component').get('ref')
        bullet_macro_id = src_weapon_macro.find('./macro/properties/bullet').get('class')

        # read weapon component+bullet macro (try existing mod file first, in case it has other modifications)
        weapon_component = (read_xml(out_weapon_component_filename, allow_fail=True) or
                            read_src(mod.src_components.get(weapon_component_id)))
        bullet_macro = (read_xml(out_bullet_macro_filename, allow_fail=True) or
                        read_src(mod.src_macros.get(bullet_macro_id)))

        for path, key, value_template in WEAPON_COMPONENT_MAPPINGS:
            set_xml(weapon_component, path, key, value_template, row, label='weapon_component')

        for path, key, value_template in WEAPON_MACRO_MAPPINGS:
            set_xml(weapon_macro, path, key, value_template, row, label='weapon_macro')

        for path, key, value_template in BULLET_MACRO_MAPPINGS:
            set_xml(bullet_macro, path, key, value_template, row, label='bullet_macro')

        write_xml(out_weapon_component_filename, weapon_component)
        write_xml(out_weapon_macro_filename, weapon_macro)
        write_xml(out_bullet_macro_filename, bullet_macro)

        mod.mod_components.append((row['weapon_component_id'],
                                   'extensions/{}{}{}'.format(mod.mod_name, rel_path, row['weapon_component_id'])))
        mod.mod_macros.append((row['weapon_macro_id'],
                               'extensions/{}{}{}'.format(mod.mod_name, rel_path, row['weapon_macro_id'])))
        mod.mod_macros.append((row['bullet_macro_id'],
                               'extensions/{}{}{}'.format(mod.mod_name, rel_path, row['bullet_macro_id'])))

        ware = mod.old_wares and mod.old_wares.find('./add/ware[@id="{}"]'.format(row['ware_component_id']))
        ware = ware or mod.src_wares.find('./ware[@id="{}"]'.format(row['base_weapon_macro'][:-6]))
        for path, key, value_template in WARE_MAPPINGS:
            set_xml(ware, path, key, value_template, row, label='weapon_macro')
        mod.mod_wares.append(ware)


def compile_ships(mod, rel_path='/mod/ships/'):
    page_id = 20101
    t_id = 100000
    page_ts = []
    mod.mod_ts[page_id] = page_ts
    ships_path = mod.mod_path+rel_path
    os.makedirs(ships_path, exist_ok=True)

    reader = csv.DictReader(open(mod.mod_path+'/ships.csv'))
    for row in reader:
        _id = row['id']
        row.update(
            ship_macro_id='ship_{id}_macro'.format(**row),
            ship_component_id='ship_{id}'.format(**row),
            ware_macro_id='ship_{id}_macro'.format(**row),
            ware_component_id='ship_{id}'.format(**row),
            page_id=page_id, t_name_id=t_id, t_basename_id=t_id+1, t_description_id=t_id+2, 
            t_variation_id=t_id+3, t_short_variation_id=t_id+4)
        page_ts.append((row['t_name_id'], row['name']))
        page_ts.append((row['t_basename_id'], row['basename']))
        page_ts.append((row['t_description_id'], row['description']))
        page_ts.append((row['t_variation_id'], row['variation']))
        page_ts.append((row['t_short_variation_id'], row['shortvariation']))
        t_id += 10

        out_ship_component_filename = ships_path+row['ship_component_id']+'.xml'
        out_ship_macro_filename = ships_path+row['ship_macro_id']+'.xml'

        # read ship macro (try existing mod file first, in case it has other modifications)
        ship_macro_id = row['base_ship_macro']
        src_ship_macro = read_src(mod.src_macros.get(ship_macro_id))
        ship_macro = read_xml(out_ship_macro_filename, allow_fail=True) or src_ship_macro
        ship_component_id = src_ship_macro.find('./macro/component').get('ref')

        # read ship component (try existing mod file first, in case it has other modifications)
        ship_component = (read_xml(out_ship_component_filename, allow_fail=True) or
                          read_src(mod.src_components.get(ship_component_id)))

        for path, key, value_template in SHIP_COMPONENT_MAPPINGS:
            set_xml(ship_component, path, key, value_template, row, label='ship_component')

        for path, key, value_template in SHIP_MACRO_MAPPINGS:
            set_xml(ship_macro, path, key, value_template, row, label='ship_macro')

        write_xml(out_ship_component_filename, ship_component)
        write_xml(out_ship_macro_filename, ship_macro)

        mod.mod_components.append((row['ship_component_id'],
                                   'extensions/{}{}{}'.format(mod.mod_name, rel_path, row['ship_component_id'])))
        mod.mod_macros.append((row['ship_macro_id'],
                               'extensions/{}{}{}'.format(mod.mod_name, rel_path, row['ship_macro_id'])))

        ware = mod.old_wares and mod.old_wares.find('./add/ware[@id="{}"]'.format(row['ware_component_id']))
        ware = ware or mod.src_wares.find('./ware[@id="{}"]'.format(row['base_ship_macro'][:-6]))
        for path, key, value_template in WARE_MAPPINGS:
            set_xml(ware, path, key, value_template, row, label='ship_macro')
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

    compile_weapons(mod)
    compile_ships(mod)

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



