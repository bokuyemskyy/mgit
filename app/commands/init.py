from argparse import _SubParsersAction

from .command import cmd
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
    parser.set_defaults(func=cmd_init)


@cmd(req_repo=False)
def cmd_init(args) -> None:
    existed = False
    try:
        repo = GitRepository.load(args.path, 1)
        existed = True
    except Exception:
        repo = GitRepository.init(args.path)
        pass

    if existed:
        logger.info(f"Reinitialized repository in {repo.worktree}")
    else:
        logger.info(f"Initialized repository in {repo.worktree}")
