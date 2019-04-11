import logging
import xml.etree.ElementTree as ET

logger = logging.getLogger('x4.' + __name__)


def read_xml(filepath, allow_fail=False):
    try:
        xml = ET.parse(filepath)
    except Exception as e:
        if allow_fail:
            logger.info('read_xml failed', extra=dict(filepath=filepath, allow_fail=allow_fail))
            return
        logger.exception('read_xml error!', extra=dict(filepath=filepath, allow_fail=allow_fail))
        raise
    return xml


def get_macros(src_path):
    xml = read_xml(src_path+'/index/macros.xml')
    return {e.get('name'): e.get('value').replace('\\', '/') for e in xml.findall('./entry')}


def get_components(src_path):
    xml = read_xml(src_path+'/index/components.xml')
    return {e.get('name'): e.get('value').replace('\\', '/') for e in xml.findall('./entry')}


def get_wares(src_path, allow_fail=False):
    return read_xml(src_path+'/libraries/wares.xml', allow_fail=allow_fail)


def write_xml(filename, xml):
    with open(filename, 'wb') as of:
        xml.write(of, encoding='utf-8', xml_declaration=True)


def set_xml(xml, path, key, value_template, row, label):
    el = xml.find(path)
    if el is None:
        logger.warning("path '{}' not found in {}".format(path, label))
        exit(0)
    try:
        value = value_template.format(**row)
    except Exception:
        logger.error('set_xml: {}, {}'.format(value_template, row), exc_info=True)
        exit(0)
    el.set(key, value)
    return True