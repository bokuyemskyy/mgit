from app.repository import repository_find, object_find, object_read
from app.objects import GitObject
from app.cli import logger


def setup_parser(subparsers):
    parser = subparsers.add_parser("cat-file", help="Cat the content of an object")
    parser.add_argument(
        "type",
        metavar="type",
        choices=["blob", "commit", "tag", "tree"],
        help="Specify the object type",
    )
    parser.add_argument("object", metavar="object", help="Object to display")
    parser.set_defaults(func=command_cat_file)


def command_cat_file(args):
    repo = repository_find()
    cat_file(repo, args.object, args.type.encode())


def cat_file(repo, sha: str, fmt=None):
    obj = object_read(repo, object_find(repo, sha, fmt=fmt))
    if not isinstance(obj, GitObject):
        raise ValueError(f"Not an object: {sha}")
    logger.info(obj.serialize().decode("ascii"))
