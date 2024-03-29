#!/usr/bin/env python3.7

import re
import os
import glob
import logging

logger = logging.getLogger('x4.' + __name__)
vdf_pat = re.compile(r'[\t ]*"\d+"[\t ]+"(.*)"')


def get_steam_folders():
    vdf_path = os.path.expanduser('~/.local/share/Steam/steamapps/libraryfolders.vdf')
    if not os.path.exists(vdf_path):
        logger.error('~/.local/share/Steam/steamapps/libraryfolders.vdf does not exist.. exiting')
        exit(-1)
    yield os.path.expanduser('~/.local/share/Steam/steamapps/common')
    with open(vdf_path) as vdf_file:
        for line in vdf_file:
            match = vdf_pat.findall(line)
            if match:
                yield f'{match[0]}/steamapps/common'


def get_game_path():
    for folder in get_steam_folders():
        for path in glob.iglob(f'{folder}/*/X4'):
            return os.path.dirname(path)
    logger.error('X4 game path not found.. exiting')
    exit(-1)


def link_game_path():
    game_path = get_game_path()
    if os.path.lexists('game'):
        os.unlink('game')
    os.symlink(game_path, 'game')


def gen_setup_py():
    pwd = os.getcwd()
    link_game_path()
    with open('config.py', 'w') as config_file:
        config_file.write('# script generated by {pwd}/setup.py\n')
        config_file.write(f'PWD = "{pwd}"\n')
        config_file.write(f'X4 = "{pwd}/game"\n')
        config_file.write(f'SRC = "{pwd}/src"\n')
        config_file.write(f'MODS = "{pwd}/mods"\n')
        config_file.write(f'OBJS = "{pwd}/objs"\n')
        config_file.write(f'THUMBS = "{pwd}/thumbs"\n')


if __name__ == '__main__':
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)
    gen_setup_py()
