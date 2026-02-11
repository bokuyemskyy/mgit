import os
from argparse import _SubParsersAction
from typing import Dict, List, Set

from app.cli import logger
from app.repository import GitIndex, GitRepository

from .command import cmd


def setup_parser(subparsers: _SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "rm", help="Remove files from the working tree and from the index"
    )
    parser.add_argument("path", nargs="+", help="Files to remove")
    parser.add_argument(
        "--cached",
        dest="cached",
        action="store_true",
        help="Unstage and remove paths only from the index, not from working tree",
    )
    parser.add_argument(
        "-r",
        dest="recursive",
        action="store_true",
        help="Allow recursive removal when a leading directory name is given",
    )
    parser.set_defaults(func=cmd_rm)


@cmd(req_repo=True)
def cmd_rm(args, repo: GitRepository) -> None:
    rm(repo, args.path, cached=args.cached, recursive=args.recursive)


def rm(
    repo: GitRepository,
    paths: List[str],
    cached=False,
    recursive=False,
):

    dirs_to_remove: Set[str] = set()
    files_to_remove: Set[str] = set()
    entries_to_remove: Dict[str, str] = {}

    for path in paths:
        abspath = os.path.realpath(path)

        if os.path.commonpath([abspath, repo.worktree]) != repo.worktree:
            raise Exception(f"path is outside of worktree: {path}")

        if abspath.startswith(repo.gitdir):
            raise Exception(f"pathspec '{path}' did not match any files")

        if os.path.isdir(abspath):
            if not recursive:
                raise Exception(f"not removing {path} recursively without -r")
            for root, dirs, files in os.walk(abspath):
                if ".git" in dirs:
                    dirs.remove(".git")
                for file in files:
                    files_to_remove.add(os.path.join(root, file))
                for dir in dirs:
                    dirs_to_remove.add(os.path.join(root, dir))

            dirs_to_remove.add(abspath)
        elif os.path.isfile(abspath):
            files_to_remove.add(abspath)
        else:
            entries_to_remove[abspath] = path

    index = GitIndex.read(repo)

    kept_entries = []
    files_removed_from_index = []

    for entry in index.entries:
        abspath = repo.fs.resolve(entry.name, root="worktree")

        if abspath in entries_to_remove:
            del entries_to_remove[abspath]
        elif abspath in files_to_remove:
            files_removed_from_index.append(abspath)
            files_to_remove.remove(abspath)
        else:
            kept_entries.append(entry)

    for _, path in entries_to_remove.items():
        raise Exception(f"pathspec '{path}' did not match any files")

    # Now, we handle files_removed_from_index, files_to_remove, dirs_to_remove

    if not cached:
        for abspath in files_to_remove:
            if os.path.exists(abspath):
                logger.info(f"removing {abspath} from the filesystem")
                os.remove(abspath)
            else:
                raise Exception(f"pathspec '{abspath}' did not match any files")
        for abspath in files_removed_from_index:
            if os.path.exists(abspath):
                logger.info(f"removing {abspath} from the filesystem")
                os.remove(abspath)
            else:
                pass  # Fine because we found and removed that file from index
        for abspath in dirs_to_remove:
            if os.path.exists(abspath):
                logger.info(f"removing {abspath} from the filesystem")
                os.rmdir(abspath)

    index.entries = kept_entries
    index.write(repo)
