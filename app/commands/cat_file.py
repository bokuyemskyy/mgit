from argparse import _SubParsersAction

from .command import cmd
from app.cli import logger
from app.objects import GitObject
from app.repository import GitRepository


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


def cat_file(repo: GitRepository, sha: str, fmt=None):
    obj = repo.objects.read(repo.objects.find(sha, fmt=fmt))
    if not isinstance(obj, GitObject):
        raise ValueError(f"Not an object: {sha}")
    logger.info(obj.serialize().decode("ascii"))
