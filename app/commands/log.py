import re
from argparse import _SubParsersAction
from datetime import datetime, timezone
from typing import Set

from app.cli import logger
from app.objects import GitCommit
from app.repository import GitRepository
from app.repository.branch import get_current_branch

from .command import cmd

# ANSI color codes
YELLOW = "\033[33m"
RESET = "\033[0m"


def setup_parser(subparsers: _SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "log",
        help="Show history of a commit",
    )
    parser.add_argument("commit", default="HEAD", nargs="?", help="Starting commit")
    parser.set_defaults(func=cmd_log)


@cmd(req_repo=True)
def cmd_log(args, repo: GitRepository) -> None:
    seen: Set[str] = set()

    try:
        tail_sha = repo.objects.find(args.commit)
    except ValueError:
        raise Exception(f"ambiguous argument {args.commit}: could not find commit")
    except FileNotFoundError:
        raise Exception(
            f"your current branch '{get_current_branch(repo)}' does not have any commits yet"
        )

    for sha in iterate_commits(repo, tail_sha, seen):
        commit = repo.objects.read(sha)

        if not isinstance(commit, GitCommit):
            raise ValueError(f"Object {sha} is not a commit")

        print_commit(commit, sha)


def iterate_commits(repo: GitRepository, sha: str, seen: Set[str]):
    if sha in seen:
        return

    seen.add(sha)
    commit = repo.objects.read(sha)

    if not isinstance(commit, GitCommit):
        raise ValueError(f"Object {sha} is not a commit")

    parents = commit.kvlm.get(b"parent")
    for parent in parents:
        parent_sha = parent.decode("ascii")
        yield from iterate_commits(repo, parent_sha, seen)

    yield sha


def print_commit(commit: GitCommit, sha: str):
    kvlm = commit.kvlm

    logger.info(f"{YELLOW}commit {sha}{RESET}")

    authors = kvlm.get(b"author")
    for author_bytes in authors:
        author_str = author_bytes.decode("utf-8")

        match = re.search(r"^(.*) (<.*>) ([0-9]+) (.*)$", author_str)

        if match:
            identity = f"{match.group(1)} {match.group(2)}"
            timestamp = int(match.group(3))
            tz_offset = match.group(4)

            readable_date = datetime.fromtimestamp(timestamp, timezone.utc).strftime(
                "%a %b %d %H:%M:%S %Y"
            )

            logger.info(f"Author: {identity}")
            logger.info(f"Date:   {readable_date} {tz_offset}")
        else:
            logger.info(f"Author: {author_str}")

    message = kvlm.get_message().decode("utf-8")

    logger.info("")
    for line in message.splitlines():
        logger.info(f"    {line}")
    logger.info("")
