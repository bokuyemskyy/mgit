import os
from argparse import _SubParsersAction

from app.cli import logger
from app.objects import GitBlob
from app.repository import GitIgnore, GitIndex, GitObjects, GitRepository
from app.repository.branch import get_current_branch
from app.repository.commit import tree_to_dict

from .command import cmd

# ANSI color codes
RED = "\033[31m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RESET = "\033[0m"


def setup_parser(subparsers: _SubParsersAction) -> None:
    parser = subparsers.add_parser("status", help="Show the working tree status")
    parser.set_defaults(func=cmd_status)


@cmd(req_repo=True)
def cmd_status(args, repo: GitRepository) -> None:
    index = GitIndex.read(repo)

    cmd_status_branch(repo)
    cmd_status_head_index(repo, index)
    cmd_status_index_worktree(repo, index)


def cmd_status_branch(repo: GitRepository):
    branch = get_current_branch(repo)

    if branch:
        logger.info(f"On branch {CYAN}{branch}{RESET}")
    else:
        logger.info(f"HEAD detached at {repo.objects.find('HEAD')}")

    logger.info("")


def cmd_status_head_index(repo, index: GitIndex):
    logger.info("Changes to be committed:")

    try:
        head = tree_to_dict(repo, "HEAD")
    except FileNotFoundError:
        head = {}

    for entry in index.entries:
        if entry.name in head:
            if head[entry.name] != entry.sha:
                logger.info(f"\t{YELLOW}modified: {entry.name}{RESET}")
            head.pop(entry.name)
        else:
            logger.info(f"\t{GREEN}added:    {entry.name}{RESET}")

    for entry in head.keys():
        logger.info(f"\t{RED}deleted:  {entry}{RESET}")

    logger.info("")


def cmd_status_index_worktree(repo: GitRepository, index: GitIndex):
    logger.info("Changes not staged for commit:")

    ignore = GitIgnore.read(repo)

    gitdir_prefix = repo.gitdir + os.path.sep

    all_files = list()

    for root, _, files in os.walk(repo.worktree, True):
        if root == repo.gitdir or root.startswith(gitdir_prefix):
            continue
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, repo.worktree)
            all_files.append(rel_path)

    for entry in index.entries:
        full_path = os.path.join(repo.worktree, entry.name)

        if not os.path.exists(full_path):
            logger.info(f"\t{RED}deleted:  {entry.name}{RESET}")
        else:
            stat = os.stat(full_path)

            ctime_ns = entry.ctime[0] * 10**9 + entry.ctime[1]
            mtime_ns = entry.mtime[0] * 10**9 + entry.mtime[1]
            if (stat.st_ctime_ns != ctime_ns) or (stat.st_mtime_ns != mtime_ns):
                with open(full_path, "rb") as f:
                    data = f.read()

                    obj = GitBlob.deserialize(data)
                    raw = GitObjects.raw(obj)
                    new_sha = GitObjects.hash(raw)

                    if not (entry.sha == new_sha):
                        logger.info(f"\t{YELLOW}modified: {entry.name}{RESET}")

        if entry.name in all_files:
            all_files.remove(entry.name)

    logger.info("")
    logger.info("Untracked files:")

    for file in all_files:
        if not ignore.check_ignore(file):
            logger.info(f"\t{RED}{file}{RESET}")
