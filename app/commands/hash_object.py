import os
from argparse import _SubParsersAction

from app.cli import logger
from app.objects import GitBlob, GitCommit, GitObject, GitTag, GitTree
from app.repository import GitObjects, GitRepository

from .command import cmd


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
    parser.set_defaults(func=cmd_hash_object)


@cmd(req_repo=False)
def cmd_hash_object(args) -> None:
    if not os.path.isfile(args.path):
        raise FileNotFoundError(f"No such file: {args.path}")

    with open(args.path, "rb") as obj_file:
        data = obj_file.read()

    object_class: type[GitObject]
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

    obj = object_class.deserialize(data)
    raw = GitObjects.raw(obj)
    sha = GitObjects.hash(raw)

    if args.write:
        repo = GitRepository.load()
        sha = repo.objects.write(obj)

    logger.info(sha)
