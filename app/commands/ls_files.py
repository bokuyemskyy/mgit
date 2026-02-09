from argparse import _SubParsersAction

from .command import cmd
from app.cli import logger
from app.repository import GitRepository, GitIndex
from datetime import datetime
import pwd
import grp


def setup_parser(subparsers: _SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "ls-files",
        help="List stage files",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Show all details")

    parser.add_argument("commit", default="HEAD", nargs="?", help="Starting commit")
    parser.set_defaults(func=cmd_ls_files)


@cmd(req_repo=True)
def cmd_ls_files(args, repo: GitRepository):
    index = GitIndex.read(repo)

    if args.verbose:
        logger.info(
            f"Index file format v{index.version}, has {len(index.entries)} entries."
        )

    for e in index.entries:
        logger.info(e.name)
        if args.verbose:
            entry_type = {
                0b1000: "regular file",
                0b1010: "symlink",
                0b1110: "git link",
            }[e.mode_type]
            logger.info(f"  {entry_type} with perms: {e.mode_perms:o}")
            logger.info(f"  on blob: {e.sha}")
            logger.info(
                f"  created: {datetime.fromtimestamp(e.ctime[0])}.{e.ctime[1]}, modified: {datetime.fromtimestamp(e.mtime[0])}.{e.mtime[1]}"
            )
            logger.info(f"  device: {e.dev}, inode: {e.ino}")
            logger.info(
                f"  user: {pwd.getpwuid(e.uid).pw_name} ({e.uid})  group: {grp.getgrgid(e.gid).gr_name} ({e.gid})"
            )
            logger.info(f"  flags: stage={e.stage} assume_valid={e.assume_valid}")
