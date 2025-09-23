from app.repository import repository_find, object_find, object_read
from app.objects import GitObject


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
    repository = repository_find()
    cat_file(repository, args.object, args.type.encode())


def cat_file(repository, sha: str, fmt=None):
    object = object_read(repository, object_find(repository, sha, fmt=fmt))
    if not isinstance(object, GitObject):
        raise ValueError(f"Not an object: {sha}")
    print(object.serialize().decode("ascii"))
