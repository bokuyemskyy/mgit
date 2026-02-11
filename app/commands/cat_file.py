import sys
from argparse import _SubParsersAction

from app.objects import GitObject
from app.repository import GitRepository

from .command import cmd


def setup_parser(subparsers: _SubParsersAction) -> None:
    parser = subparsers.add_parser("cat-file", help="Cat the content of an object")
    parser.add_argument(
        "type",
        metavar="type",
        choices=["blob", "commit", "tag", "tree"],
        help="Specify the object type",
    )
    parser.add_argument("object", metavar="object", help="Object to display")
    parser.set_defaults(func=cmd_cat_file)


@cmd(req_repo=True)
def cmd_cat_file(args, repo) -> None:
    cat_file(repo, args.object, args.type.encode())


def cat_file(repo: GitRepository, name: str, fmt=None):
    sha = repo.objects.find(name, fmt=fmt)
    obj = repo.objects.read(sha)

    if not isinstance(obj, GitObject):
        raise ValueError(f"not an object: {sha}")

    sys.stdout.buffer.write(obj.serialize())
