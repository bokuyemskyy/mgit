from app.cli import logger

from app.repository import (
    repository_find,
    object_write,
    object_hash,
    object_raw,
    GitCommit,
    GitBlob,
    GitTag,
    GitTree,
)


def setup_parser(subparsers):
    parser = subparsers.add_parser(
        "hash-object",
        help="Compute the hash of an object and optionally write it to the database",
    )
    parser.add_argument(
        "-t",
        metavar="type",
        dest="type",
        choices=["blob", "commit", "tag", "tree"],
        default="blob",
        help="Specify the type",
    )
    parser.add_argument(
        "-w",
        dest="write",
        action="store_true",
        help="Write the object into the database",
    )
    parser.add_argument("path", help="Source for the object")
    parser.set_defaults(func=command_hash_object)


def command_hash_object(args):
    match args.type.encode():
        case b"commit":
            object_class = GitCommit
        case b"tree":
            object_class = GitTree
        case b"tag":
            object_class = GitTag
        case b"blob":
            object_class = GitBlob
        case _:
            raise ValueError(f"Unknown object type: {args.type}")

    with open(args.path, "rb") as obj_file:
        data = obj_file.read()

    obj = object_class.deserialize(data)
    raw = object_raw(obj)
    sha = object_hash(raw)

    if args.write:
        repo = repository_find()
        sha = object_write(obj, repo)

    logger.info(sha)
