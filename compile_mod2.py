# ElementTree xpath ref: https://docs.python.org/3/library/xml.etree.elementtree.html#elementtree-xpath

import os
import sys
import yaml
import glob
from lib.x4lib import get_config
from xml.etree import ElementTree


def modify_attrib_value(modifier, attrib_val):
    """
    modifier: 
        first char indicates action =, *, /
        followed by a decimal or float value
        eg. *1.2 would take existing attribute value and muliply it by 1.2
    attrib_val: string containing integer or floating point number
    """
    if modifier.startswith('='):
        return modifier[1:]
    elif modifier.startswith('+'):
        if attrib_val is None:
            return None
        return f'{float(attrib_val) + float(modifier[1:]):1.1f}'
    elif modifier.startswith('-'):
        if attrib_val is None:
            return None
        return f'{float(attrib_val) - float(modifier[1:]):1.1f}'
    elif modifier.startswith('*'):
        if attrib_val is None:
            return None
        return f'{float(attrib_val) * float(modifier[1:]):1.1f}'
    elif modifier.startswith('/'):
        if attrib_val is None:
            return None
        return f'{float(attrib_val) / float(modifier[1:]):1.1f}'
    elif modifier.startswith(':'):  # list
        attrib_val_list = attrib_val.strip().split(' ')
        modifier_list = modifier[1:].strip().split(' ')
        for modifier2 in modifier_list:
            modifier2_val = modifier2[1:]
            if modifier2.startswith('?'):
                # check if value exists, if not present then leave this tag unchanged
                if modifier2_val not in attrib_val_list:
                    return attrib_val
            elif modifier2.startswith('+'):
                # append value if present
                if modifier2_val not in attrib_val_list:
                    attrib_val_list.append(modifier2_val)
            elif modifier2.startswith('-'):
                # remove value if present
                if modifier2_val in attrib_val_list:
                    attrib_val_list.remove(modifier2_val)
        return ' '.join(attrib_val_list)

    raise Exception(f'Unexpected modifier: {modifier} for value {attrib_val}')



def find_and_replace(xml, modifiers):
    for pat, val in modifiers.items():
        if '@' in pat and isinstance(val, (str, list)):
            val_list = [val] if isinstance(val, str) else val 
            pat2, attrib = pat.rsplit('@', 1)
            els = xml.findall(f'./{pat2}')
            for el in els:
                attrib_val = el.attrib.get(attrib, None)
                for val2 in val_list:
                    if attrib_val or val2.startswith('='):
                        el.attrib[attrib] = attrib_val = modify_attrib_value(modifier=val2, attrib_val=attrib_val)
        elif pat.endswith('>APPEND>'):
            val_list = [val] if isinstance(val, str) else val 
            els = xml.findall(f'./{pat[:-8]}')
            for el in els:
                for val2 in val_list:
                    if '*COCKPIT' in val2:
                        cel = xml.find('./component/connections/connection[@name="con_cockpit"]/offset/position')
                        x = float(cel.attrib["x"])
                        y = float(cel.attrib["y"])
                        z = float(cel.attrib["z"])
                        if '*COCKPIT-TOP*' in val2:
                            val2 = val2.replace('*COCKPIT-TOP*', f'x="{x}" y="{y+2}" z="{z-2}"')
                        if '*COCKPIT-BOTTOM*' in val2:
                            val2 = val2.replace('*COCKPIT-BOTTOM*', f'x="{x}" y="{y-2.5}" z="{z-5}"')
                        if '*COCKPIT-LEFT*' in val2:
                            val2 = val2.replace('*COCKPIT-LEFT*', f'x="{x-2.25}" y="{y+1.75}" z="{z-5}"')
                        if '*COCKPIT-RIGHT*' in val2:
                            val2 = val2.replace('*COCKPIT-RIGHT*', f'x="{x+2.25}" y="{y+1.75}" z="{z-5}"')
                    new_el = ElementTree.fromstring(val2)
                    new_el.tail = '\n'
                    el.append(new_el)

        elif '>CLONE>' in pat:
            pat, src_el_pat = pat.split('>CLONE>', 1)
            el = xml.find(f'./{pat}')
            src_el = el.find(f'./{src_el_pat}')
            if not src_el:
                print(f'Err: not found {pat} | {src_el_pat}')
            else:
                new_el = ElementTree.fromstring(ElementTree.tostring(src_el))
                new_el.attrib.update(val)
                new_el.tail = '\n'
                el.append(new_el)
            
        else:        
            elements = xml.findall(f'./{pat}')
            for el in elements:
                find_and_replace(el, val)


def write_xml(filename, xml):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    outstr = ElementTree.tostring(xml.getroot(), xml_declaration=True).replace(b'version=\'1.0\' encoding=\'us-ascii\'', b'version="1.0"').replace(b' />', b'/>')
    with open(filename, 'wb') as of:
        of.write(outstr)



def write_index_file(filepathname, entries):    
    root = ElementTree.Element('diff')
    root.text = root.tail = '\n'
    add = ElementTree.Element('add', sel='/index')
    add.text = add.tail = '\n'
    root.append(add)
    for name, value in entries:
        entry = ElementTree.Element('entry', name=name, value=value)
        entry.tail = '\n'
        add.append(entry)
    write_xml(filepathname, ElementTree.ElementTree(root))



def apply_yaml(entries, yaml_data, src_path, mod_path):
    mod_name = mod_path.rsplit('/', 1)[-1]
    for pat, modifiers in yaml_data.items():
        file_type = 'macros' if 'macro' in pat else f'components'
        files = glob.glob(src_path+'/**/'+pat, recursive=True)
        for filepathname in files:
            filename = filepathname.rsplit('/', 1)[-1]
            entry_name = filename.rsplit('.',1)[0]
            out_filename = f'{mod_path}/{file_type}/{filename}'
            entry = (entry_name, f'extensions\\{mod_name}\\{file_type}\\{entry_name}')
            if entry in entries:
                print(f'\t\t{filepathname} -> {out_filename}')
                print("\t\t\tWarning: trying update the same file twice, currently this will discard whatever modification was applied earlier")

            xml = ElementTree.parse(filepathname)
            find_and_replace(xml, modifiers)
            write_xml(out_filename, xml)
            entries.add(entry)
            # print(f'\t\tAdding {filepathname} -> {out_filename}')

        print(f'\tApplying pattern {pat:65}: {len(files):3} files matched')


def compile_mod(src_path, mod_path, pat):
    entries = set()
    for cfg_filename in glob.glob(f'{mod_path}/mod_*.yaml'):
        if pat and pat not in cfg_filename:
            continue
        with open(cfg_filename) as cfg_file:
            yaml_data = yaml.load(cfg_file)
        print(f'Applying {cfg_filename}:')
        apply_yaml(entries, yaml_data, src_path, mod_path)
        print()

    macros_list = [entry for entry in entries if 'macros' in entry[1]]
    components_list = [entry for entry in entries if 'components' in entry[1]]

    write_index_file(f'{mod_path}/index/macros.xml', macros_list)
    write_index_file(f'{mod_path}/index/components.xml', components_list)
    
    print (f'Compiled {len(macros_list)} macros, {len(components_list)} components')
        


if __name__ == '__main__':
    args = sys.argv[1:]
    mod_path = os.getcwd()


    args = sys.argv[1:]
    if len(args) < 1:
        logger.info("%s <mod_name>", sys.argv[0])
    else:
        mod_name=args[0]
        pat = args[1] if len(args)>1 else None
        config=get_config()
        compile_mod(src_path=config.SRC, mod_path=f'{config.MODS}/{mod_name}', pat=pat)



        

