import logging
import sys
import os
import os.path
from copy import deepcopy
from xml.etree import ElementTree
import csv

logger = logging.getLogger('x4.' + __name__)


def require_python_version(major, minor):
    if sys.version_info.major < major or sys.version_info.minor < minor:
        logger.error('This script requires python 3.6 or higher.')
        exit(0)


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
    def read_xml(cls, filepath, allow_fail=False):
        try:
            xml = ElementTree.parse(filepath)
        except Exception:
            if allow_fail:
                logger.info('read_xml failed', extra=dict(filepath=filepath, allow_fail=allow_fail))
                return
            logger.exception('read_xml error!', extra=dict(filepath=filepath, allow_fail=allow_fail))
            raise
        return xml

    @classmethod
    def write_xml(cls, filename, xml):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
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
        if value != '':
            # skip on blank value
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

    @classmethod
    def get_ts(cls, src_path, allow_fail=False, language=44):
        return cls.read_xml(src_path + '/t/0001-L{:03d}.xml'.format(language), allow_fail=allow_fail)

    @classmethod
    def read_csv(cls, filename: str, csv_data: dict):
        reader_rows = csv.reader(open(filename))
        header = None
        rows = None
        for row in reader_rows:
            col0 = row[0].strip().lower()
            if col0.startswith('h'):
                ware_type = col0[1:].lstrip()
                header = [h for h in row[1:] if h != '']
                rows = csv_data.setdefault(ware_type, [])
            elif col0 == 'd':
                rows.append({h: d for h, d in zip(header, row[1:])})

    @classmethod
    def pat_replace(cls, text, pat, repl_fn):
        out = []
        matches = pat.finditer(text)
        start = 0
        for m in matches:
            out.extend([
                text[start:m.start()],
                repl_fn(*m.groups()),
            ])
            start = m.end()
        out.append(text[start:])
        had_replacements = start > 0
        return u''.join(out), had_replacements

