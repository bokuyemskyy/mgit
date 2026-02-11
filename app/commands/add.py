import os
from argparse import _SubParsersAction
from typing import List, Set

from app.objects import GitBlob
from app.repository import GitIgnore, GitIndex, GitIndexEntry, GitRepository

from .command import cmd


def setup_parser(subparsers: _SubParsersAction) -> None:
    parser = subparsers.add_parser("add", help="Add file contents to the index")
    parser.add_argument("path", nargs="+", help="Files to add")
    parser.set_defaults(func=cmd_add)


@cmd(req_repo=True)
def cmd_add(args, repo: GitRepository) -> None:
    add(repo, args.path)


def add(repo: GitRepository, paths: List[str], skip_missing=False):
    files_to_add: Set[str] = set()

    ignore = GitIgnore.read(repo)

    for path in paths:
        abspath = os.path.realpath(path)

        if os.path.commonpath([abspath, repo.worktree]) != repo.worktree:
            raise Exception(f"path is outside of worktree: {path}")

        if abspath.startswith(repo.gitdir):
            raise Exception(f"pathspec '{path}' did not match any files")

        if os.path.isdir(abspath):
            for root, dirs, files in os.walk(abspath):
                if ".git" in dirs:
                    dirs.remove(".git")
                for file in files:
                    full_path = os.path.join(root, file)
                    relpath = os.path.relpath(full_path, repo.worktree)

                    if not ignore.check_ignore(relpath):
                        files_to_add.add(full_path)
        elif os.path.isfile(abspath):
            relpath = os.path.relpath(abspath, repo.worktree)
            if not ignore.check_ignore(relpath):
                files_to_add.add(abspath)
        elif not skip_missing:
            raise Exception(f"path does not exist: {path}")

    index = GitIndex.read(repo)

    entry_map = {entry.name: i for i, entry in enumerate(index.entries)}

    for abspath in files_to_add:
        relpath = os.path.relpath(abspath, repo.worktree)

        with open(abspath, "rb") as f:
            data = f.read()

            obj = GitBlob.deserialize(data)

            sha = repo.objects.write(obj)

            stat = os.stat(abspath)

            new_entry = GitIndexEntry(
                ctime=(int(stat.st_ctime), stat.st_ctime_ns % 10**9),
                mtime=(int(stat.st_mtime), stat.st_mtime_ns % 10**9),
                dev=stat.st_dev,
                ino=stat.st_ino,
                mode_type=0b1000,
                mode_perms=0o644,
                uid=stat.st_uid,
                gid=stat.st_gid,
                fsize=stat.st_size,
                sha=sha,
                assume_valid=False,
                stage=0,
                name=relpath,
            )

            if relpath in entry_map:
                index.entries[entry_map[relpath]] = new_entry
            else:
                index.entries.append(new_entry)

    index.entries.sort(key=lambda x: x.name)
    index.write(repo)
