#!/usr/bin/python3

"""
Pack mods/{mod name}/* mod files into {game dir}/extensions/{mod name}/* (cat+dat)
Use: python3 pack_mod.py {mod name}
"""

import sys
import logging
from pack_x4 import pack

logger = logging.getLogger('x4.' + __name__)

try:
    import config
except ImportError:
    logger.exception('config.py not found, please run setup.sh before using this script!')
    exit(1)


if __name__ == '__main__':
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)

    args = sys.argv[1:]
    if len(args) < 1:
        logger.info("%s <mod_name>", sys.argv[0])
    else:
        mod_name = args[0]
        pack(src='{}/{}/'.format(config.MODS, mod_name),
             dst='{}/extensions/{}/'.format(config.X4, mod_name))



