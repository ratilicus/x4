#!/usr/bin/env python3.7

import logging
import argparse
import glob
from lib.x4lib import get_config, require_python_version
from extract_x4 import CatParser
from compile_mod import X4ModCompiler
from pack_mod import pack_mod

require_python_version(3, 7)
logger = logging.getLogger('x4.' + __name__)

VERBOSITY = {1: logging.WARNING, 2: logging.INFO, 3: logging.DEBUG}


def setup_logging(verbosity):
    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(VERBOSITY.get(verbosity, logging.WARNING))


def cmd_extract_x4(args):
    setup_logging(args.verbosity)
    config = get_config()

    if args.file:
        out_path = '{}/custom'.format(config.PWD)
    else:
        out_path = config.SRC

    parser = CatParser(
        out_path=out_path,
        scripts_only=args.scripts,
        signatures=args.signatures,
    )

    if args.file:
        parser.extract(cat_filename=args.file)

    else:
        method = parser.list if args.list else parser.extract
        cats = sorted(glob.iglob(f'{config.X4}/*.cat'))
        for cat in cats:
            method(cat_filename=cat)


def cmd_compile_mod(args):
    setup_logging(args.verbosity)
    compiler = X4ModCompiler(mod_name=args.mod_name, config=get_config())
    compiler.compile()


def cmd_pack_mod(args):
    setup_logging(args.verbosity)
    pack_mod(mod_name=args.mod_name, config=get_config())


def get_parser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser_extract = subparsers.add_parser('extract', aliases=['x'], help='Extract cab files to src dir')
    group = parser_extract.add_mutually_exclusive_group(required=True)
    group.add_argument('-s', '--scripts', action='store_true', help='Extract scripts only')
    group.add_argument('-a', '--all', action='store_true', help='Extract all files')
    group.add_argument('-l', '--list', action='store_true', help='List only')
    group.add_argument('-f', '--file', help='Extract cab file')
    parser_extract.add_argument('--signatures', action='store_true', help='Extract signatures also')
    parser_extract.add_argument('-v', '--verbosity', type=int, default=1, help='Verbose output')
    group.set_defaults(func=cmd_extract_x4)

    parser_compile = subparsers.add_parser('compile', aliases=['c'], help='Compile cvs in mod dir into xml files from src')
    parser_compile.add_argument('mod_name', help='<mod name>')
    parser_compile.add_argument('-v', '--verbosity', type=int, default=1, help='Verbose output')
    parser_compile.set_defaults(func=cmd_compile_mod)

    parser_pack = subparsers.add_parser('pack', aliases=['p'], help='Pack mod dir and put into game extensions dir')
    parser_pack.add_argument('mod_name', help='<mod name>')
    parser_pack.add_argument('-v', '--verbosity', type=int, default=1, help='Verbose output')
    parser_pack.set_defaults(func=cmd_pack_mod)

    parser.set_defaults(func=lambda a: parser.print_usage())
    return parser


if __name__ == '__main__':
    parser = get_parser()
    args = parser.parse_args()
    args.func(args)
