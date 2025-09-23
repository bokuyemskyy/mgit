import sys
import argparse

from commands import init, cat_file, hash_object, log, ls_tree


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title="Commands", dest="command")
    subparsers.required = True

    for module in [init, cat_file, hash_object, log, ls_tree]:
        module.setup_parser(subparsers)

    return parser


def main(argv=sys.argv[1:]):
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
