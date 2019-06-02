import re
import logging
import os.path
from whoosh.index import create_in, open_dir
from whoosh.qparser import MultifieldParser
from whoosh.fields import SchemaClass, TEXT, KEYWORD, ID, STORED, NUMERIC

logger = logging.getLogger('x4.' + __name__)
fields_pat = re.compile(r'([a-zA-Z0-9_]+):')


class Manager(object):
    def __init__(self, schema):
        self._q = None  # stores last query, for debugging
        self._qf = None  # stores last query fields, for debugging
        self.schema = schema
        self.ix = None

    def get_or_create_index(self, recreate=False):
        index_path = f'db/{self.schema._meta["name"]}'
        if not os.path.exists(index_path):
            os.makedirs(index_path)
            self.ix = create_in(index_path, self.schema)
            return self.ix, True
        else:
            self.ix = open_dir(index_path)
            return self.ix, False

    def create(self, **kwargs):
        if self.ix is None:
            self.ix = self.get_or_create_index()
        kwargs['all'] = '\n'.join(map(str, (kwargs[k] for k in self.schema._meta['search_fields']
                                            if k in kwargs and kwargs[k] is not None)))
        w = self.ix.writer()
        w.add_document(**kwargs)
        w.commit()

    def search(self, search_str, fields=None, limit=3):
        self._q = None
        if self.ix is None:
            self.ix, _ = self.get_or_create_index()
        if not fields:
            search_fields = fields_pat.findall(search_str)
            fields = ['all'] + [f for f in search_fields if f in self.schema._fields]
        parser = MultifieldParser(fields, self.ix.schema)
        self._q = parser.parse(search_str)
        self._qf = fields
        logger.info("query str: %s", self._q)
        logger.info("query fields: %s", self._qf)
        with self.ix.searcher() as s:
            hits = s.search(self._q, limit=limit)
            for hit in hits:
                yield hit


def prep_model(cls):
    """ prep schema decorator
        allows setting name and other attributes on schema
    """
    meta = cls._clsfields.pop('Meta')
    if not hasattr(meta, 'search_fields'):
        meta.search_fields = list(cls._clsfields)
    cls._clsfields['all'] = TEXT(stored=True)
    instance = cls()
    instance._meta = {'name': meta.name, 'search_fields': getattr(meta, 'search_fields')}
    instance.objects = Manager(schema=instance)
    return instance
