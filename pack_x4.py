#!/usr/bin/python3

"""
Pack {src} mod files into {dst} (cat+dat)
Use: python3 pack_x4.py {src} {dst}
"""

import os
import sys
import os.path
import hashlib
import shutil


def pack(src, dst):
    os.makedirs(dst, exist_ok=True)
    with open('{}ext_01.cat'.format(dst), 'wb') as cat_file,\
         open('{}ext_01.dat'.format(dst), 'wb') as dat_file:
        src_offset = len(src)
        for src_path, dirs, files in os.walk(src):
            path = src_path[src_offset:]
            for filename in files:
                src_filename = os.path.join(src_path, filename)
                if not path:
                    dst_filename = os.path.join(dst, filename)
                    shutil.copy(src_filename, dst_filename)
                else:
                    file_data = open(src_filename, 'r').read().encode('utf-8')
                    digest = hashlib.md5(file_data).hexdigest()
                    rel_filename = os.path.join(path, filename)
                    stat = os.stat(src_filename)
                    cat_file.write('{} {} {} {}\n'.format(rel_filename, len(file_data),
                                                          int(stat.st_mtime), digest).encode('utf-8'))
                    dat_file.write(file_data)


if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) < 2:
        print("%s <src> <dst>" % sys.argv[0])
    else:
        pack(src=args[0].rstrip('/') + '/',
             dst=args[1].rstrip('/') + '/')


