from app.repository import repository_find, object_hash


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
    repository = None

    if args.write:
        repository = repository_find()

    with open(args.path, "rb") as object_file:
        sha = object_hash(object_file, args.type.encode(), repository)
        print(sha)
