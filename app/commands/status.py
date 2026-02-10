from argparse import _SubParsersAction
import os

from .command import cmd
from app.cli import logger
from app.objects import GitTree, GitBlob
from app.repository import GitRepository, GitIndex, GitIgnore, GitObjects


def setup_parser(subparsers: _SubParsersAction) -> None:
    parser = subparsers.add_parser("status", help="Show the working tree status")
    parser.set_defaults(func=cmd_status)


@cmd(req_repo=True)
def cmd_status(args, repo: GitRepository) -> None:
    index = GitIndex.read(repo)

    cmd_status_branch(repo)
    cmd_status_head_index(repo, index)
    cmd_status_index_worktree(repo, index)


def get_current_branch(repo: GitRepository):
    content = repo.fs.file_read("HEAD", binary=False)

    if content.startswith("ref: refs/heads/"):
        return content[16:-1]
    else:
        return False


def cmd_status_branch(repo: GitRepository):
    branch = get_current_branch(repo)

    if branch:
        logger.info(f"On branch {branch}")
    else:
        logger.info(f"HEAD detached at {repo.objects.find('HEAD')}")

    logger.info("")


def tree_to_dict(repo: GitRepository, ref, prefix=""):
    result = dict()

    sha = repo.objects.find(ref, fmt=b"tree")
    tree = repo.objects.read(sha)

    assert isinstance(tree, GitTree)

    for leaf in tree.items:
        full_path = os.path.join(prefix, leaf.path)

        is_subtree = leaf.mode.startswith(b"04")

        if is_subtree:
            result.update(tree_to_dict(repo, leaf.sha, full_path))
        else:
            result[full_path] = leaf.sha
    return result


def cmd_status_head_index(repo, index: GitIndex):
    logger.info("Changes to be committed:")

    head = tree_to_dict(repo, "HEAD")

    for entry in index.entries:
        if entry.name in head:
            if head[entry.name] != entry.sha:
                logger.info(f"\tmodified: {entry.name}")
            head.pop(entry.name)
        else:
            logger.info(f"\tadded:    {entry.name}")

    for entry in head.keys():
        logger.info(f"\tdeleted:  {entry}")

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
            logger.info(f"\tdeleted:  {entry.name}")
        else:
            stat = os.stat(full_path)

            ctime_ns = entry.ctime[0] * 10**9 + entry.ctime[1]
            mtime_ns = entry.mtime[0] * 10**9 + entry.mtime[1]
            if (stat.st_ctime_ns != ctime_ns) or (stat.st_mtime_ns != mtime_ns):
                with open(full_path, "rb") as file:
                    data = file.read()

                    obj = GitBlob.deserialize(data)
                    raw = GitObjects.raw(obj)
                    new_sha = GitObjects.hash(raw)

                    if not (entry.sha == new_sha):
                        logger.info(f"\tmodified: {entry.name}")

        if entry.name in all_files:
            all_files.remove(entry.name)

    logger.info("")
    logger.info("Untracked files:")

    for file in all_files:
        if not ignore.check_ignore(file):
            logger.info(f"\t{file}")
