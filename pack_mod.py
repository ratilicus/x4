#!/usr/bin/python3

"""
Pack mods/{mod name}/* mod files into {game dir}/extensions/{mod name}/* (cat+dat)
Use: python3 pack_mod.py {mod name}
"""

import sys
from pack_x4 import pack

try:
    import config
except ImportError:
    print('config.py not found, please run setup.sh before using this script!')
    exit(1)


if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) < 1:
        print("%s <mod_name>" % sys.argv[0])
    else:
        mod_name = args[0]
        pack(src='{}/{}/'.format(config.MODS, mod_name),
             dst='{}/extensions/{}/'.format(config.X4, mod_name))



