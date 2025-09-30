import os
from argparse import _SubParsersAction

from .command import command
from app.cli import logger
from app.repository import GitRepository
from app.objects import GitCommit, GitTree, GitTag, GitBlob


def setup_parser(subparsers: _SubParsersAction) -> None:
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


@command(requires_repo=False)
def command_hash_object(args) -> None:
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

    if not os.path.isfile(args.path):
        raise FileNotFoundError(f"No such file: {args.path}")
    with open(args.path, "rb") as obj_file:
        data = obj_file.read()

    obj = object_class.deserialize(data)
    raw = GitRepository.object_raw(obj)
    sha = GitRepository.object_hash(raw)

    if args.write:
        repo = GitRepository.find()
        sha = repo.object_write(obj)

    logger.info(sha)
