from __future__ import annotations

import os
from configparser import ConfigParser
from typing import Dict, Union, Optional
from .filesystem import GitFilesystem
from .objects import GitObjects
from .references import GitReferences
from .config import default_config

RefTree = Dict[str, Union[str, "RefTree"]]


class RepositoryNotFound(Exception):
    pass


class GitRepository:
    def __init__(self, worktree: str, gitdir: Optional[str] = None) -> None:
        self.worktree = os.path.realpath(worktree)

        if gitdir is None:
            self.gitdir = os.path.join(self.worktree, ".git")
        else:
            self.gitdir = os.path.realpath(gitdir)

        self.fs = GitFilesystem(self.worktree, self.gitdir)

        config_path = self.fs.resolve("config")
        self.config: ConfigParser = ConfigParser(strict=False)

        if self.fs.file_exists("config"):
            self.config.read(config_path)
        else:
            self.config = default_config()

        self.objects = GitObjects(self.fs)
        self.refs = GitReferences(self.fs)

    @classmethod
    def _create_initial_structure(cls, worktree: str, gitdir: str):
        fs = GitFilesystem(worktree, gitdir)

        os.makedirs(worktree, exist_ok=True)
        os.makedirs(gitdir, exist_ok=True)
        for dir_name in ["branches", "objects", "refs/tags", "refs/heads"]:
            fs.dir_ensure(dir_name)

        files_to_create = {
            "description": "Unnamed repository\n",
            "HEAD": "ref: refs/heads/main\n",
        }
        for filename, content in files_to_create.items():
            if not fs.file_exists(filename):
                fs.file_ensure(filename, content=content)

        config_path = fs.resolve("config")
        with open(config_path, "w", encoding="utf-8") as config_file:
            default_config().write(config_file)

    @classmethod
    def init(cls, path: str) -> GitRepository:
        worktree = os.path.realpath(path)
        gitdir = os.path.join(worktree, ".git")

        cls._create_initial_structure(worktree, gitdir)

        return cls(worktree, gitdir)

    @classmethod
    def load(cls, at: str = ".", max_depth: int = 64) -> GitRepository:
        path = os.path.realpath(at)
        depth = 0

        while True:
            if depth >= max_depth:
                raise RepositoryNotFound(
                    f"No git repository found within {max_depth} levels"
                )

            worktree_path = path
            gitdir_path = os.path.join(path, ".git")

            if os.path.isdir(gitdir_path):
                return cls(worktree_path, gitdir_path)

            parent = os.path.realpath(os.path.join(path, ".."))
            if parent == path:
                raise RepositoryNotFound("No git repository found")

            path = parent
            depth += 1
