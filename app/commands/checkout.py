from argparse import _SubParsersAction
import os

from .command import cmd
from app.repository import GitRepository
from app.objects import GitCommit, GitTree, GitBlob


def setup_parser(subparsers: _SubParsersAction) -> None:
    parser = subparsers.add_parser("checkout", help="Checkout a commit")
    parser.add_argument("commit", help="The object to checkout")
    parser.add_argument("path", help="The empty directory to checkout on.")
    parser.set_defaults(func=cmd_checkout)


@cmd(req_repo=True)
def cmd_checkout(args, repo: GitRepository) -> None:
    sha = repo.objects.find(args.commit)
    obj = repo.objects.read(sha)

    if not isinstance(obj, GitCommit):
        raise ValueError(f"Object is not a commit: {sha}")

    obj = repo.objects.read(obj.kvlm[b"tree"][0].decode("ascii"))

    if os.path.exists(args.path):
        if not os.path.isdir(args.path):
            raise Exception(f"Not a directory {args.path}")
        if os.listdir(args.path):
            raise Exception(f"Not empty {args.path}")
    else:
        os.makedirs(args.path)

    tree_checkout(repo, obj, os.path.realpath(args.path))


def tree_checkout(repo: GitRepository, tree, path):
    for item in tree.items:
        obj = repo.objects.read(item.sha)
        dest = os.path.join(path, item.path)

        if isinstance(obj, GitTree):
            os.mkdir(dest)
            tree_checkout(repo, obj, dest)
        elif isinstance(obj, GitBlob):
            with open(dest, "wb", encoding="utf-8") as obj_file:
                obj_file.write(obj.data)
