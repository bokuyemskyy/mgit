import os
from argparse import _SubParsersAction

from .command import command
from app.cli import logger
from app.repository import GitRepository
from app.objects import GitTree


def setup_parser(subparsers: _SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "ls-tree",
        help="Print a tree object",
    )
    parser.add_argument(
        "-r", dest="recursive", action="store_true", help="Recurse into sub-trees"
    )
    parser.set_defaults(func=command_ls_tree)


@command(requires_repo=True)
def command_ls_tree(args, repo) -> None:
    ls_tree(repo, args.tree, args.recursive)


def ls_tree(repo: GitRepository, name: str, recursive: bool = False, prefix=""):
    sha = repo.object_find(name, fmt="tree")
    obj = repo.object_read(name)

    if not isinstance(obj, GitTree):
        raise ValueError(f"Object is not a tree: {sha}")

    for item in obj.items:
        if len(item.mode) == 5:
            type = item.mode[0:1]
        else:
            type = item.mode[0:2]

        match type:
            case b"04":
                type = "tree"
            case b"10":
                type = "blob"
            case b"12":
                type = "blob"
            case b"16":
                type = "commit"
            case _:
                raise Exception(f"Unknown object type: {item.mode}")

        if not (recursive and type == "tree"):
            logger.info(
                f"{'0' * (6 - len(item.mode)) + item.mode.decode('ascii')} {type} {item.sha}\t{os.path.join(prefix, item.path)}"
            )
        else:
            ls_tree(repo, item.sha, recursive, os.path.join(prefix, item.path))
