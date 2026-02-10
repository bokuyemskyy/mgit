from argparse import _SubParsersAction
import os
from typing import List, Tuple


from .rm import rm
from .command import cmd
from app.objects import GitBlob
from app.repository import GitRepository, GitIndex, GitIndexEntry, GitObjects


def setup_parser(subparsers: _SubParsersAction) -> None:
    parser = subparsers.add_parser("commit", help="Record changes to the repository")
    parser.add_argument("-m", metavar="message", dest="message", help="Commit message")
    parser.set_defaults(func=cmd_add)


@cmd(req_repo=True)
def cmd_add(args, repo: GitRepository) -> None:
    add(repo, args.path)


def add(repo: GitRepository, paths: List[str], delete=False, skip_missing=False):
    rm(repo, paths, delete=False, skip_missing=True)

    worktree_prefix = repo.worktree + os.sep

    pair_paths: Tuple[str, str] = set()

    for path in paths:
        abspath = os.path.abspath(path)
        if not abspath.startswith(worktree_prefix):
            raise Exception(f"Path is outside of worktree: {abspath}")
        if not os.path.isfile(abspath):
            raise Exception(f"Not a file: {abspath}")
        relpath = os.path.relpath(abspath, repo.worktree)
        pair_paths.add((abspath, relpath))

    index = GitIndex.read(repo)

    for abspath, relpath in pair_paths:
        with open(abspath, "rb") as file:
            data = file.read()

            obj = GitBlob.deserialize(data)
            raw = GitObjects.raw(obj)
            sha = GitObjects.hash(raw)

            stat = os.stat(abspath)

            ctime_s = int(stat.st_ctime)
            ctime_ns = stat.st_ctime_ns % 10**9
            mtime_s = int(stat.st_mtime)
            mtime_ns = stat.st_mtime_ns % 10**9

            entry = GitIndexEntry(
                ctime=(ctime_s, ctime_ns),
                mtime=(mtime_s, mtime_ns),
                dev=stat.st_dev,
                ino=stat.st_ino,
                mode_type=0b1000,
                mode_perms=0o644,
                uid=stat.st_uid,
                gid=stat.st_gid,
                fsize=stat.st_size,
                sha=sha,
                assume_valid=False,
                stage=False,
                name=relpath,
            )
            index.entries.append(entry)

    index.write(repo)
