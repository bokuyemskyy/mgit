import os
from app.repository import (
    object_read,
    object_find,
    repository_find,
    GitTree,
    GitRepository,
)


def setup_parser(subparsers):
    parser = subparsers.add_parser(
        "ls-tree",
        help="Print a tree object",
    )
    parser.add_argument(
        "-r", dest="recursive", action="store_true", help="Recurse into sub-trees"
    )
    parser.set_defaults(func=command_ls_tree)


def command_ls_tree(args):
    repo = repository_find()
    ls_tree(repo, args.tree, args.recursive)


def ls_tree(repo: GitRepository, name: str, recursive: bool = False, prefix=""):
    sha = object_find(repo, name, fmt="tree")
    obj = object_read(repo, name)

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
            print(
                f"{"0" * (6 - len(item.mode)) + item.mode.decode("ascii")} {type} {item.sha}\t{os.path.join(prefix, item.path)}"
            )
        else:
            ls_tree(repo, item.sha, recursive, os.path.join(prefix, item.path))
