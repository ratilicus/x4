import xml.etree.ElementTree as ET


def get_macros(src_path):
    xml = ET.parse(src_path+'/index/macros.xml')
    return {e.get('name'): e.get('value').replace('\\', '/') for e in xml.findall('./entry')}


def get_components(src_path):
    xml = ET.parse(src_path+'/index/components.xml')
    return {e.get('name'): e.get('value').replace('\\', '/') for e in xml.findall('./entry')}


def get_wares(src_path, allow_fail=False):
    try:
        xml = ET.parse(src_path+'/libraries/wares.xml')
    except:
        if allow_fail:
            return
        raise
    return xml


def read_xml(filepath, allow_fail=False):
    try:
        xml = ET.parse(filepath)
    except Exception as e:
        if allow_fail:
            return
        raise
    return xml


def write_xml(filename, xml):
    with open(filename, 'wb') as of:
        xml.write(of, encoding='utf-8', xml_declaration=True)


def set_xml(xml, path, key, value_template, row, label):
    el = xml.find(path)
    if el is None:
        print("path '{}' not found in {}".format(path, label))
        ET.dump(xml)
        exit(0)
    try:
        value = value_template.format(**row)
    except Exception:
        print('set_xml: {}, {}'.format(value_template, row))
        raise
    el.set(key, value)
