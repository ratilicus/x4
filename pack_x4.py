#!/usr/bin/env python3

"""
Pack {src} mod files into {dst} (cat+dat)
Use: python3 pack_x4.py {src} {dst}
"""

import os
import sys
import os.path
import hashlib
import shutil
import logging

logger = logging.getLogger('x4.' + __name__)


def pack_path(src, dst):
    os.makedirs(dst, exist_ok=True)
    with open('{}ext_01.cat'.format(dst), 'wb') as cat_file,\
         open('{}ext_01.dat'.format(dst), 'wb') as dat_file:
        src_offset = len(src)
        for src_path, dirs, files in os.walk(src):
            path = src_path[src_offset:]
            for filename in files:
                src_filename = os.path.join(src_path, filename)
                if not path:
                    dst_filename = os.path.join(dst.rstrip('/'), filename)
                    shutil.copy(src_filename, dst_filename)
                else:
                    file_data = open(src_filename, 'rb').read()
                    digest = hashlib.md5(file_data).hexdigest()
                    rel_filename = os.path.join(path, filename)
                    stat = os.stat(src_filename)
                    cat_file.write('{} {} {} {}\n'.format(rel_filename, len(file_data),
                                                          int(stat.st_mtime), digest).encode('utf-8'))
                    dat_file.write(file_data)


if __name__ == '__main__':
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)

    args = sys.argv[1:]
    if len(args) < 2:
        logger.info("%s <src> <dst>", sys.argv[0])
    else:
        pack_path(src=args[0].rstrip('/') + '/',
             dst=args[1].rstrip('/') + '/')


