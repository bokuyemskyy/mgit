from argparse import _SubParsersAction

from .command import cmd
from app.cli import logger
from app.repository import GitRepository
from app.objects import GitCommit


def setup_parser(subparsers: _SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "log",
        help="Show history of a commit",
    )
    parser.add_argument("commit", default="HEAD", nargs="?", help="Starting commit")
    parser.set_defaults(func=cmd_log)


@cmd(req_repo=True)
def cmd_log(args, repo: GitRepository) -> None:
    seen = set()

    for sha in iterate_commits(repo, repo.objects.find(args.commit), seen):
        commit = repo.objects.read(sha)
        if not isinstance(commit, GitCommit):
            raise ValueError(f"Object {sha} is not a commit")
        print_commit(commit, sha)


def iterate_commits(repo: GitRepository, sha, seen):
    if sha in seen:
        return

    seen.add(sha)
    commit = repo.objects.read(sha)

    if not isinstance(commit, GitCommit):
        raise ValueError(f"Object {sha} is not a commit")

    parents = commit.kvlm.get(b"parent", [])

    if not isinstance(parents, list):
        parents = [parents]

    for parent in parents:
        yield from iterate_commits(repo, parent, seen)

    yield sha


def print_commit(commit: GitCommit, sha):
    kvlm = commit.kvlm

    logger.info(f"commit {sha.decode('ascii')}")
    if b"author" in kvlm:
        for author in kvlm[b"author"]:
            logger.info(f"Author: {author.decode('utf-8')}")

    if b"date" in kvlm:
        for date in kvlm[b"date"]:
            logger.info(f"Date:   {date.decode('utf-8')}")

    message = kvlm.get(None, [b""])[0].decode("utf-8")

    logger.info("")
    for line in message.splitlines():
        logger.info(f"    {line}")
    logger.info("")
