from __future__ import annotations
import os
from configparser import ConfigParser
from typing import Dict, Union
from .filesystem import GitFilesystem
from .objects import GitObjects
from .references import GitReferences
from .config import default_config


RefTree = Dict[str, Union[str, "RefTree"]]


class RepositoryNotFound(Exception):
    pass


class GitRepository:
    def __init__(self, path: str, create=True) -> None:
        self.worktree = os.path.realpath(path)
        self.gitdir = os.path.join(self.worktree, ".git")
        self.fs = GitFilesystem(self.worktree, self.gitdir)

        if os.path.exists(self.worktree):
            if not os.path.isdir(self.worktree):
                raise NotADirectoryError(f"{self.worktree} is not a directory")
        else:
            os.makedirs(self.worktree, exist_ok=True)

        if create:
            os.makedirs(self.gitdir, exist_ok=True)
            for dir_name in ["branches", "objects", "refs/tags", "refs/heads"]:
                self.fs.dir_ensure(dir_name)
            files_to_create = {
                "description": "Unnamed repository\n",
                "HEAD": "ref: refs/heads/main\n",
            }
            for filename, content in files_to_create.items():
                if not self.fs.file_exists(filename):
                    self.fs.file_ensure(filename, content=content)

        config_path = self.fs.resolve_path("config")

        if self.fs.file_exists("config"):
            self.config: ConfigParser = ConfigParser(strict=False)
            self.config.read(config_path)
        else:
            with open(config_path, "w", encoding="utf-8") as config_file:
                self.config: ConfigParser = default_config()
                self.config.write(config_file)

        self.objects = GitObjects(self.fs)
        self.refs = GitReferences(self.fs)

    @classmethod
    def find(cls, at: str = ".", max_depth: int = 64) -> GitRepository:
        path = os.path.realpath(at)
        depth = 0
        while True:
            if depth >= max_depth:
                raise RepositoryNotFound(
                    f"No git repository found within {max_depth} levels"
                )
            gitdir_path = os.path.join(path, ".git")
            if os.path.isdir(gitdir_path):
                return cls(path, create=True)
            parent = os.path.realpath(os.path.join(path, ".."))
            if parent == path:
                raise RepositoryNotFound("No git repository found")
            path = parent
            depth += 1

    @classmethod
    def create(cls, path: str) -> GitRepository:
        return cls(path, create=True)
