from argparse import _SubParsersAction

from .command import cmd
from app.repository import GitRepository, GitIgnore
from app.cli import logger


def setup_parser(subparsers: _SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "check-ignore", help="Show which files are ignored by .gitignore"
    )
    parser.add_argument(
        "path",
        nargs="+",
        help="Paths to check",
    )
    parser.set_defaults(func=cmd_check_ignore)


@cmd(req_repo=True)
def cmd_check_ignore(args, repo: GitRepository) -> None:
    ignore = GitIgnore.read(repo)
    for path in args.path:
        if ignore.is_ignored(path):
            logger.info(f"{path}")
