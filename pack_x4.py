#!/usr/bin/python

import os
import errno
import sys
import os.path
import hashlib
import shutil


def make_path(path):
    # in python 3 this can go away since it has a parameter to ignore path exists errors
    try:
        os.makedirs(path)
    except OSError as error:
        pass


def pack(src, dst):
    make_path(dst)
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
                    cat_file.write('{} {} {} {}\n'.format(rel_filename, len(file_data), int(stat.st_mtime), digest).encode('utf-8'))
                    dat_file.write(file_data)


if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) < 2:
        print("%s <src> <dst>" % sys.argv[0])
    else:
        src = args[0].rstrip('/') + '/'
        dst = args[1].rstrip('/') + '/'
        pack(src, dst)


