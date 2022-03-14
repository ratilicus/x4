"""

pre-load data:
    parse src/base/t/0001-l044.xml   (* need to add this)
    parse src/base/libraries/wares.xml   (* need to add this)
    merge src/ego_dlc_split/libraries/wares.xml   (* need to add this)
    merge src/ego_dlc_terran/libraries/wares.xml   (* need to add this)

parse mod:
    clone ship or equipment
        get wares entry   (* need to add this)
        parse assets/.... macro -> write moded macro
        parse assets/.... component -> write moded macro
        add to index/components.xml
        add to index/macros.xml
        add to libraries/wares.xml   (* need to add this)
        add to t/0001-l044.xml   (* need to add this)
        
"""

import logging
import os
import sys
import glob
import re
from lib.x4lib import get_config
from lib.patched_element_tree import ElementTree
from lib.patch_xml import patch

logger = logging.getLogger('x4.' + __name__)
cache = {}


def search_macros(src_path, macro_id):
    for filename in sorted(glob.glob(f'{src_path}/*/index/macros.xml')):
        xml = cache.setdefault(filename, ElementTree.parse(filename))
        entry = xml.find(f'./entry[@name="{macro_id}"]')
        if entry is not None:
            return entry.get('value')




def search_ts(src_path, t_id_str):
    page_id, t_id = t_id_str.strip('{} ').replace(' ', '').split(',')
    for t_filename in sorted(glob.glob(f'{src_path}/*/t/*044.xml')):
        t_file = cache.setdefault(t_filename, ElementTree.parse(t_filename))
        t_entry = t_file.find(f'./page[@id="{page_id}"]/t[@id="{t_id}"]')
        if t_entry is not None:
            return t_entry.text


def resolve_t(src_path, t_id_str):
    text = search_ts(src_path, t_id_str)
    if text:
        sub_t_ids = re.findall(r'{\d+,\d+}|[(][^\]]+[)]', text)
        for sub_t_id in sub_t_ids:
            if sub_t_id.startswith('{'):
                sub_t_id_text = resolve_t(src_path, sub_t_id)
            else:
                sub_t_id_text = ''
            text = text.replace(sub_t_id, sub_t_id_text)
    return text and text.replace('\\', '')


def preload_wares(src_path):
    if 'wares' in cache:
        return cache['wares']
    cache['wares'] = wares_xml = ElementTree.parse(f'{src_path}/base/libraries/wares.xml')
    #for patch_filename in sorted(glob.glob(f'{src_path}/ego_dlc_*/libraries/wares.xml')):
    #    patch_xml = ElementTree.parse(patch_filename)
    #    patch(wares_xml, patch_xml)

    return wares_xml


def search_wares(src_path, ware_id_str):
    print(f'Searching: {ware_id_str}')
    wares_xml = preload_wares(src_path)
    for ware in wares_xml.findall(f'./ware[@id="{ware_id_str}"]'):
        ware_id = ware.get('id')
        ware_name = resolve_t(src_path, ware.get('name'))
        #description = resolve_t(src_path, ware.get('description'))
        ware_group = ware.get('group')
        ware_transport = ware.get('transport')
        ware_volume = ware.get('volume')
        ware_tags = ware.get('tags')
        comp_el = ware.find('./component')
        macro_id = comp_el.get('ref') if comp_el is not None else None
        macro_path = search_macros(src_path, macro_id) if macro_id else None
        print(f'{ware_id:32} | {str(ware_name):30} | {ware_group} | {ware_transport} | {ware_volume} | {ware_tags} | {macro_path}')




if __name__ == '__main__':
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)

    args = sys.argv[1:]
    if len(args) < 1:
        logger.info('%s <ware_id (regex: "^ship_.{3}_s_" to find all small ships)>', sys.argv[0])
        exit(0)

    config=get_config()
    print(f'Searching: {args}')
    search_wares(src_path=config.SRC, ware_id_str=args[0])
    


