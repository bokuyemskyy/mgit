from argparse import _SubParsersAction
from datetime import datetime, timezone
from typing import Optional

from app.cli import logger
from app.objects import GitCommit
from app.repository import GitIndex, GitRepository
from app.repository.branch import update_ref
from app.repository.commit import tree_from_index
from app.repository.config import get_user_from_config

from .command import cmd


def setup_parser(subparsers: _SubParsersAction) -> None:
    parser = subparsers.add_parser("commit", help="Record changes to the repository")
    parser.add_argument("-m", metavar="message", dest="message", help="Commit message")
    parser.set_defaults(func=cmd_commit)


@cmd(req_repo=True)
def cmd_commit(args, repo: GitRepository) -> None:
    index = GitIndex.read(repo)

    if not index.entries:
        logger.info("Nothing to commit (create/copy files and use 'mgit add')")
        return

    tree_sha = tree_from_index(repo, index)

    try:
        parent_sha = repo.objects.find("HEAD")
    except FileNotFoundError:
        parent_sha = None

    author = get_user_from_config(repo.config)
    commit_sha = create_commit(
        repo,
        tree_sha,
        parent_sha,
        author,
        args.message,
    )

    update_ref(repo, commit_sha)
    logger.info(f"[{commit_sha[:7]}] {args.message.splitlines()[0]}")


def create_commit(
    repo: GitRepository,
    tree_sha: str,
    parent_sha: Optional[str],
    author: str,
    message: str,
) -> str:
    commit = GitCommit()
    commit.kvlm.set(b"tree", tree_sha.encode("ascii"))

    if parent_sha:
        commit.kvlm.set(b"parent", parent_sha.encode("ascii"))

    now = datetime.now(timezone.utc).astimezone()
    timestamp = now.strftime("%s %z")

    author_data_bytes = f"{author} {timestamp}".encode("utf-8")
    commit.kvlm.set(b"author", author_data_bytes)
    commit.kvlm.set(b"committer", author_data_bytes)
    commit.kvlm.set_message(message.strip().encode("utf-8") + b"\n")

    sha = repo.objects.write(commit)

    return sha
