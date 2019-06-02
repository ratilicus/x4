#!/usr/bin/env python3.7

import re
import logging
import sys

from tqdm import tqdm
from lib.x4lib import get_config, require_python_version, ModUtilMixin
from lib import models

t_pat = re.compile(r'\([^\)]+\)|{(\d+),[ ]?(\d+)}')

require_python_version(3, 7)
logger = logging.getLogger('x4.' + __name__)


class Indexer(ModUtilMixin):

    def __init__(self, config):
        self.config = config
        self.out_file = f'{config.SRC}/index.csv'
        self.ts = self.get_ts(config.SRC)
        self.wares = self.get_wares(config.SRC)

    def find_t(self, page_id=None, t_id=None):
        if page_id is None and t_id is None:
            return ''
        el = self.ts.find(f'./page[@id="{page_id}"]/t[@id="{t_id}"]')
        return el.text if el is not None else ''

    def get_label(self, text):
        if not text:
            return ''
        out, had_replacements = self.pat_replace(text, pat=t_pat, repl_fn=self.find_t)
        if had_replacements:
            return self.get_label(out)
        return out

    def index_ts(self):
        ts = self.get_ts(self.config.SRC)
        model = models.T
        ix, new = model.objects.get_or_create_index()
        if not new:
            if ix.doc_count() > 34000:
                return
        logger.info('Indexing Ts')
        for page in tqdm(ts.findall('./page')):
            pageid = page.get('id')
            for t in tqdm(page.findall('./t')):
                tid = t.get('id')
                model.objects.create(
                    id=f'{pageid},{tid}',
                    pageid=pageid,
                    tid=tid,
                    value=self.get_label(t.text.strip())
                )

    def index_wares(self):
        model = models.Ware
        ix, new = model.objects.get_or_create_index()
        if not new:
            if ix.doc_count() > 900:
                return
        logger.info('Indexing Wares')
        for ware in tqdm(self.wares.findall('./ware')):
            _id = ware.get('id')
            production_el = ware.find('production')
            production_name = self.get_label(production_el.get('name') or '') if not production_el is None else ''
            component_el = ware.find('component')
            component_ref = component_el.get('ref') if not component_el is None else ''
            restriction_el = ware.find('restriction')
            license = restriction_el.get('license') if not restriction_el is None else ''
            owner_els = ware.findall('owner')
            factions = ' '.join(el.get('faction') for el in owner_els)
            model.objects.create(
                id=_id,
                name=self.get_label(ware.get('name')),
                description=self.get_label(ware.get('description')),
                group=ware.get('group'),
                transport=ware.get('transport'),
                volume=ware.get('volume'),
                tags=ware.get('tags'),
                production=production_name,
                macro=component_ref,
                license=license,
                factions=factions,
            )

    def index_all(self):
        self.index_ts()
        self.index_wares()


def search(search_str, fields=None, limit=3):
    hits = models.Ware.objects.search(search_str, fields=fields, limit=limit)
    for hit in hits:
        h = hit.highlights('all', top=10)
        logger.info(f'{h}\n'
                    f'{dict(hit)}\n')


if __name__ == '__main__':
    logging.getLogger().addHandler(logging.StreamHandler())
    logging.getLogger().setLevel(logging.INFO)

    args = sys.argv[1:]
    if len(args) < 1:
        logger.info("%s -i  to index dbs", sys.argv[0])
        logger.info("%s <search text>", sys.argv[0])
    elif args[0] == '-i':
        indexer = Indexer(config=get_config())
        indexer.index_all()
    else:
        search_str = ' '.join(args)
        search(search_str)