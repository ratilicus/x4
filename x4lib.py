import logging
import os
import os.path
from copy import deepcopy
import xml.etree.ElementTree as ET

logger = logging.getLogger('x4.' + __name__)


def get_config():
    try:
        config = __import__('config')
    except ImportError:
        logger.exception('config.py not found, please run setup.sh before using this script!')
        exit(1)
    return config


class ModUtilMixin(object):

    @classmethod
    def clone(cls, xml):
        return deepcopy(xml)

    @classmethod
    def makedirs(cls, path):
        os.makedirs(path, exist_ok=True)

    @classmethod
    def read_xml(cls, filepath, allow_fail=False):
        try:
            xml = ET.parse(filepath)
        except Exception:
            if allow_fail:
                logger.info('read_xml failed', extra=dict(filepath=filepath, allow_fail=allow_fail))
                return
            logger.exception('read_xml error!', extra=dict(filepath=filepath, allow_fail=allow_fail))
            raise
        return xml

    @classmethod
    def write_xml(cls, filename, xml):
        cls.makedirs(os.path.dirname(filename))
        with open(filename, 'wb') as of:
            xml.write(of, encoding='utf-8', xml_declaration=True)

    @classmethod
    def set_xml(cls, xml, path, key, value_template, row, label):
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

    @classmethod
    def update_xml(cls, xml, row, mapping, label):
        for path, key, value_template in mapping:
            cls.set_xml(xml, path, key, value_template, row, label=label)

    @classmethod
    def get_macros(cls, src_path):
        xml = cls.read_xml(src_path + '/index/macros.xml')
        return {e.get('name'): e.get('value').replace('\\', '/') for e in xml.findall('./entry')}

    @classmethod
    def get_components(cls, src_path):
        xml = cls.read_xml(src_path + '/index/components.xml')
        return {e.get('name'): e.get('value').replace('\\', '/') for e in xml.findall('./entry')}

    @classmethod
    def get_wares(cls, src_path, allow_fail=False):
        return cls.read_xml(src_path + '/libraries/wares.xml', allow_fail=allow_fail)

