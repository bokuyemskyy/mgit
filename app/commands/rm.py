from argparse import _SubParsersAction
import os
from typing import List

from .command import cmd
from app.cli import logger
from app.objects import GitTree, GitBlob
from app.repository import GitRepository, GitIndex, GitIgnore, GitObjects


def setup_parser(subparsers: _SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "rm", help="Remove files from the working tree and from the index."
    )
    parser.add_argument("path", nargs="+", help="Files to remove")
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Remove files from filesystem (destructive!)",
    )
    parser.set_defaults(func=cmd_rm)


@cmd(req_repo=True)
def cmd_rm(args, repo: GitRepository) -> None:
    rm(repo, args.path, delete=args.force)


def rm(repo: GitRepository, paths: List[str], delete=False, skip_missing=False):
    index = GitIndex.read(repo)

    worktree_prefix = repo.worktree + os.sep

    abspaths = set()

    for path in paths:
        abspath = os.path.abspath(path)
        if not os.path.realpath(abspath).startswith(os.path.realpath(worktree_prefix)):
            raise Exception(f"Path is outside of worktree: {abspath}")
        abspaths.add(abspath)

    kept_entries = list()

    to_remove = list()

    for entry in index.entries:
        full_path = repo.fs.resolve(entry.name, root="worktree")

        if full_path in abspaths:
            to_remove.append(full_path)
            abspaths.remove(full_path)
        else:
            kept_entries.append(entry)

    if len(abspaths) > 0 and not skip_missing:
        raise Exception(f"Cannot remove paths not in the index: {abspaths}")

    if delete:
        for path in to_remove:
            try:
                logger.warning(f"Removing {path} from filesystem")
                os.remove(path)
            except OSError as e:
                logger.error(f"Failed to remove {path}: {e}")

    index.entries = kept_entries
    index.write(repo)
