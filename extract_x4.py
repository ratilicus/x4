#!/usr/bin/env python3

"""
Extract xml scripts into source dir
Use: python extract_x4.py --extract
"""

import os
import sys
import os.path
import logging
from lib.x4lib import get_config, require_python_version

require_python_version(3, 5)
logger = logging.getLogger('x4.' + __name__)


class CatParser(object):
    SCRIPTS_EXT = ('.xml', '.xsd', '.xsl', '.dtd', '.lua')

    @staticmethod
    def parse_line(line):
        """
        Parse/split a single line from cat file
        :param line: (str) line from a cat file
        :return: (str, int)
        """
        try:
            # since filename can have spaces in it, we want to rsplit, and the are 4 fields so expect 3 split chars
            # Note: filenames can have spaces in them
            out_filename, out_size, timestamp, md5hex = line.rsplit(' ', 3)
            out_size = int(out_size)
        except ValueError:
            logger.exception('parse line error!', extra=dict(line=line))
            raise
        return out_filename, out_size

    @classmethod
    def is_script_file(cls, filename):
        """
        Is filename a script file
        :param filename: (str) filename
        :return: (bool) True if script else False
        """
        return filename.endswith(cls.SCRIPTS_EXT)

    @classmethod
    def is_sig_file(cls, filename):
        """
        Is filename a signature file
        :param filename: (str) filename
        :return: (bool) True if signature file else False
        """
        return filename.endswith('.sig')

    @classmethod
    def cat_files_iterator(cls, cat_filename):
        """
        Return an iterator for each file in the cat file
        :param cat_filename: path/name of cat file
        :return: yields (filename, offset, size)
        """
        offset = 0
        with open(cat_filename, "r") as cat_file:
            for line in cat_file:
                filename, size = cls.parse_line(line)
                yield filename, offset, size
                offset += size

    @classmethod
    def extract_file(cls, dat_file, out_file_path, offset, size):
        """
        Extract a single file from dat file
        :param dat_file: (file) file pointer to dat file
        :param out_file_path: (str) path/name of file to extract
        :param offset: (int) offset of file in dat file
        :param size: (int) size of file to extract
        :return: None
        """
        dat_file.seek(offset)
        data = dat_file.read(size)
        os.makedirs(out_file_path.rsplit('/', 1)[0], exist_ok=True)
        with open(out_file_path, 'wb') as out_file:
            out_file.write(data)

    def __init__(self, out_path=None, scripts_only=True, signatures=False):
        """
        Init parser
        :param out_path: (str) path to extract to
        :param scripts_only: (bool) extract/list only scripts
        :param signatures: (bool) include signatures in extraction/listing
        """
        self.out_path = out_path
        self.scripts_only = scripts_only
        self.signatures = signatures

    def list(self, cat_filename):
        """
        List files in cat file
        :param cat_filename: (str) file/path of cat file
        :return: None
        """
        files_iter = self.cat_files_iterator(cat_filename)
        for filename, offset, size in files_iter:
            if self.scripts_only:
                if self.is_script_file(filename):
                    logger.info('%60s (%10d)', filename, size)
            else:
                if not self.signatures and self.is_sig_file(filename):
                    continue
                logger.info('%60s (%10d)', filename, size)

    def extract(self, cat_filename):
        """
        Extract files from cat/dat file
        cat file is an index file for the dat file
        - cat format:
            - each row represents a single file
            - row format: "<filename> <size> <unknown> <unknown>"
            - note: filename can have spaces in it
            - offset for each file is the cumulative sum of sizes of previous files in the cat file

        :param cat_filename: (str) file/path of cat file
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
                        logger.info('%60s | %10s', cat_filename, out_file_path)
                else:
                    if not self.signatures and self.is_sig_file(filename):
                        continue
                    out_file_path = '{}/{}'.format(self.out_path, filename)
                    self.extract_file(dat_file, out_file_path, offset, size)
                    logger.info('\t%s', out_file_path)


def extract_x4(cat_path, out_path, extract, scripts_only, signatures=False):
    """
    Extract all x4 cat files
    :param cat_path: path to game .cat/.dat files
    :param out_path: path to extract the files inside the .cat/.dat files
    :param extract: (bool) extract if True else list (bool)
    :param scripts_only: (bool) extract only script files if True else all files
    :param signatures: (bool) extract signature files if True (default False)
    :return: None
    """
    
    cats = sorted(f for f in os.listdir(cat_path) if f.endswith('.cat'))
    parser = CatParser(
        out_path=out_path,
        scripts_only=scripts_only,
        signatures=signatures,
    )
    method = parser.extract if extract else parser.list
    for f in cats:
        method(cat_filename='{}/{}'.format(cat_path, f))


if __name__ == '__main__':
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)

    args = set(sys.argv[1:])
    if not args:
        logger.info("%s <--extract | --list> <--all>", sys.argv[0])
        exit(0)

    if args & {'--extract', '--list'}:
        config=get_config()
        extract_x4(
            extract='--extract' in args,
            scripts_only='--all' not in args,
            cat_path=config.X4,
            out_path=f'{config.SRC}/base',
        )
        dlcs = (f for f in os.listdir(f'{config.X4}/extensions') if f.startswith('ego_dlc_'))
        for dlc in dlcs:
            extract_x4(
                extract='--extract' in args,
                scripts_only='--all' not in args,
                cat_path=f'{config.X4}/extensions/{dlc}',
                out_path=f'{config.SRC}/{dlc}',
            )
        

    else:
        config = get_config()
        CatParser(
            out_path='{}/custom'.format(config.PWD),
            scripts_only=False,
        ).extract(cat_filename=sys.argv[1])
