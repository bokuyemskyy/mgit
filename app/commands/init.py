from argparse import _SubParsersAction

from .command import command
from app.repository import GitRepository
from app.cli import logger


def setup_parser(subparsers: _SubParsersAction) -> None:
    parser = subparsers.add_parser("init", help="Initialize an empty repository")
    parser.add_argument(
        "path",
        metavar="directory",
        nargs="?",
        default=".",
        help="Where to create the repository",
    )
    parser.set_defaults(func=command_init)


@command(requires_repo=False)
def command_init(args) -> None:
    existed = False
    try:
        GitRepository.find(args.path, 1)
        existed = True
    except Exception:
        pass

    repo = GitRepository.create(args.path)

    if existed:
        logger.info(f"Reinitialized repository in {repo.worktree}")
    else:
        logger.info(f"Initialized repository in {repo.worktree}")
