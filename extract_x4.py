#!/usr/bin/python3

"""
Extract xml scripts into source dir
Use: python extract_x4.py --extract
"""

import os
import sys
import os.path
import logging
from x4lib import get_config

logger = logging.getLogger('x4.' + __name__)


class CatParser(object):
    SCRIPTS_EXT = ('.xml', '.xsd', '.xsl', '.dtd', '.lua')

    @staticmethod
    def parse_line(line):
        """
        Parse/split a single line from cat file
        :param line:
        :return:
        """
        try:
            # since filename can have spaces in it, we want to rsplit, and the are 4 fields so expect 3 split chars
            out_filename, out_size, _, _ = line.rsplit(' ', 3)
            out_size = int(out_size)
        except ValueError as e:
            logger.exception('parse line error!', extra=dict(line=line))
            raise
        return out_filename, out_size

    def __init__(self, cat_filename, out_path, extract=False, scripts_only=True, signatures=False):
        self.out_path = out_path
        self.extract = extract
        self.scripts_only = scripts_only
        self.signatures = signatures
        if extract:
            self.extract_files(cat_filename)
        else:
            self.list_files(cat_filename)

    def is_script_file(self, filename):
        return filename.endswith(self.SCRIPTS_EXT)

    def cat_files_iterator(self, cat_filename):
        """
        Return an iterator for each file in the cat file
        :param cat_filename: path/name of cat file
        :return: yields (filename, offset, size)
        """
        offset = 0
        with open(cat_filename, "r") as cat_file:
            for line in cat_file:
                filename, size = self.parse_line(line)
                yield filename, offset, size
                offset += size

    def list_files(self, cat_filename):
        """
        List files in cat file
        :param cat_filename: file/path of cat file
        :param scripts_only: only exract script files (no binary or other)
        :return:
        """
        files_iter = self.cat_files_iterator(cat_filename)
        for filename, offset, size in files_iter:
            if self.scripts_only:
                if self.is_script_file(filename):
                    logger.info('%60s (%10d)', filename, size)
            else:
                if not self.signatures and filename.endswith('.sig'):
                    continue
                logger.info('%60s (%10d)', filename, size)

    def extract_files(self, cat_filename):
        """
        Extract files from cat/dat file
        cat file is an index file for the dat file
        - cat format:
            - each row represents a single file
            - row format: "<filename> <size> <unknown> <unknown>"
            - note: filename can have spaces in it
            - offset for each file is the cumulative sum of sizes of previous files in the cat file

        :param cat_filename: file/path of cat file
        :return:
        """
        dat_filename = cat_filename[:-4] + ".dat"
        files_iter = self.cat_files_iterator(cat_filename)
        with open(dat_filename, "rb") as dat_file:
            for filename, offset, size in files_iter:
                if self.scripts_only:
                    if self.is_script_file(filename):
                        out_file_path = '{}/{}'.format(self.out_path, filename)
                        self.extract_file(dat_file, out_file_path, offset, size)
                        logger.info('%60s (%10d)', cat_filename, out_file_path)
                else:
                    if not self.signatures and filename.endswith('.sig'):
                        continue
                    out_file_path = '{}/{}'.format(self.out_path, filename)
                    self.extract_file(dat_file, out_file_path, offset, size)
                    logger.info('\t%s', out_file_path)

    def extract_file(self, dat_file, out_file_path, offset, size):
        """
        Extract a single file from dat file
        :param dat_file: file pointer to dat file
        :param out_file_path: path/name of file to extract
        :param offset: offset of file in dat file
        :param size: size of file to extract
        :return:
        """
        dat_file.seek(offset)
        data = dat_file.read(size)
        self.write_file(out_file_path, data)

    def write_file(self, out_file_path, data):
        """
        Write file t
        :param out_file_path:
        :param data:
        :return:
        """
        os.makedirs(out_file_path.rsplit('/', 1)[0], exist_ok=True)
        with open(out_file_path, 'wb') as out_file:
            out_file.write(data)


def extract_x4(config, extract, scripts_only, signatures=False):
    cats = sorted(f for f in os.listdir(config.X4) if f.endswith('.cat'))
    for f in cats:
        c = CatParser(
            cat_filename='{}/{}'.format(config.X4, f),
            out_path=config.SRC,
            extract=extract,
            scripts_only=scripts_only,
            signatures=signatures,
        )


if __name__ == '__main__':
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)

    args = set(sys.argv[1:])
    if not args:
        logger.info("%s <--extract | --list> <--all>", sys.argv[0])
        exit(0)

    config = get_config()
    if args & {'--extract', '--list'}:
        extract_x4(extract='--extract' in args,
                   scripts_only='--all' not in args,
                   config=config)

    else:
        c = CatParser(
            cat_filename=sys.argv[1],
            out_path='{}/custom'.format(config.PWD),
            extract=True,
            scripts_only=False,
        )

