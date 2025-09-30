import os
from argparse import _SubParsersAction

from .command import command
from app.repository import GitRepository
from app.objects import GitCommit, GitTree, GitBlob


def setup_parser(subparsers: _SubParsersAction) -> None:
    parser = subparsers.add_parser("checkout", help="Checkout a commit")
    parser.add_argument("commit", help="The object to checkout")
    parser.add_argument("path", help="The empty directory to checkout on.")
    parser.set_defaults(func=command_checkout)


@command(requires_repo=True)
def command_checkout(args, repo) -> None:
    sha = repo.object_find(args.commit)
    obj = repo.object_read(sha)

    if not isinstance(obj, GitCommit):
        raise ValueError(f"Object is not a commit: {sha}")

    obj = repo.object_read(obj.kvlm[b"tree"][0].decode("ascii"))

    if os.path.exists(args.path):
        if not os.path.isdir(args.path):
            raise Exception(f"Not a directory {args.path}")
        if os.listdir(args.path):
            raise Exception(f"Not empty {args.path}")
    else:
        os.makedirs(args.path)

    tree_checkout(repo, obj, os.path.realpath(args.path))


def tree_checkout(repo, tree, path):
    for item in tree.items:
        obj = repo.object_read(item.sha)
        dest = os.path.join(path, item.path)

        if isinstance(obj, GitTree):
            os.mkdir(dest)
            tree_checkout(repo, obj, dest)
        elif isinstance(obj, GitBlob):
            with open(dest, "wb") as obj_file:
                obj_file.write(obj.data)
