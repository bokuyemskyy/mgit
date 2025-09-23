from app.repository import repository_create


def setup_parser(subparsers):
    parser = subparsers.add_parser("init", help="Initialize an empty repository")
    parser.add_argument(
        "path",
        metavar="directory",
        nargs="?",
        default=".",
        help="Where to create the repository",
    )
    parser.set_defaults(func=command_init)


def command_init(args):
    repository_create(args.path)
