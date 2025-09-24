import os
from app.repository import (
    repository_find,
    object_find,
    object_read,
    GitCommit,
    GitTree,
    GitBlob,
)


def setup_parser(subparsers):
    parser = subparsers.add_parser("checkout", help="Checkout a commit")
    parser.add_argument("commit", help="The object to checkout")
    parser.add_argument("path", help="The empty directory to checkout on.")
    parser.set_defaults(func=command_checkout)


def command_checkout(args):
    repo = repository_find()

    sha = object_find(repo, args.commit)
    obj = object_read(repo, sha)

    if not isinstance(obj, GitCommit):
        raise ValueError(f"Object is not a commit: {sha}")

    obj = object_read(repo, obj.kvlm[b"tree"][0].decode("ascii"))

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
        obj = object_read(repo, item.sha)
        dest = os.path.join(path, item.path)

        assert obj is not None

        if isinstance(obj, GitTree):
            os.mkdir(dest)
            tree_checkout(repo, obj, dest)
        elif isinstance(obj, GitBlob):
            with open(dest, "wb") as obj_file:
                obj_file.write(obj.data)
