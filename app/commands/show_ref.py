from __future__ import annotations

from argparse import _SubParsersAction

from .command import command
from app.cli import logger
from app.repository import GitRepository, RefTree


def setup_parser(subparsers: _SubParsersAction) -> None:
    parser = subparsers.add_parser("show-ref", help="Show references")
    parser.set_defaults(func=command_show_ref)


@command(requires_repo=True)
def command_show_ref(args, repo) -> None:
    refs = repo.ref_list()
    show_ref(refs, prefix="refs")


def show_ref(refs: RefTree, with_hash: bool = True, prefix: str = "") -> None:
    for name, value in refs.items():
        ref_path = f"{prefix}/{name}" if prefix else name

        if isinstance(value, str):
            logger.info(f"{value} {ref_path}" if with_hash else ref_path)
        elif isinstance(value, dict):
            show_ref(value, with_hash=with_hash, prefix=ref_path)
        else:
            raise TypeError("Unexpected ref value type")
