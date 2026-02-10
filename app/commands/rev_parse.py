from argparse import _SubParsersAction

from .command import cmd
from app.cli import logger
from app.repository import GitRepository


def setup_parser(subparsers: _SubParsersAction) -> None:
    parser = subparsers.add_parser("rev-parse", help="Parse object identifiers")

    parser.add_argument(
        "--type",
        metavar="type",
        dest="type",
        choices=["blob", "commit", "tag", "tree"],
        default=None,
        help="The expected type",
    )

    parser.add_argument("name", help="The name to parse")

    parser.set_defaults(func=cmd_rev_parse)


@cmd(req_repo=True)
def cmd_rev_parse(args, repo: GitRepository) -> None:
    if args.type:
        fmt = args.type.encode()
    else:
        fmt = None

    logger.info(repo.objects.find(args.name, fmt, follow=True))
