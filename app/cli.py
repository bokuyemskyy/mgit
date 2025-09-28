import sys
import argparse
import importlib

COMMAND_DIR = "app.commands"

COMMANDS = [
    "init",
    "cat_file",
    "hash_object",
    "log",
    "ls_tree",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title="Commands", dest="command")
    subparsers.required = True

    load_commands(subparsers)

    return parser


def load_commands(subparsers: argparse._SubParsersAction):
    for cmd_name in COMMANDS:
        try:
            module = importlib.import_module(f"{COMMAND_DIR}.{cmd_name}")
        except Exception as e:
            sys.stderr.write(f"Failed to import {cmd_name}: {e}\n")
            continue

        if hasattr(module, "setup_parser") and callable(module.setup_parser):
            module.setup_parser(subparsers)
        else:
            sys.stderr.write(f"Module {cmd_name} missing setup_parser\n")


def main(argv=sys.argv[1:]):
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
