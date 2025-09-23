import os
import configparser
from typing import Optional


class GitRepository:
    worktree: str
    gitdir: str
    config: configparser.ConfigParser

    def __init__(self, path: str, force: bool = False) -> None:
        self.worktree = path
        self.gitdir = os.path.join(path, ".git")
        self.config = configparser.ConfigParser()

        if not os.path.isdir(self.gitdir) and not force:
            raise NotADirectoryError(f"Not a git repository: {path}")

        config_file = repository_file(self, "config")

        if config_file and os.path.exists(config_file):
            self.config.read([config_file])
        elif not force:
            raise Exception("Configuration file not found")

        if not force:
            version = int(self.config.get("core", "repositoryformatversion"))
            if version != 0:
                raise Exception(f"Unsupported repositoryformatversion: {version}")


def repository_find(path: str = ".") -> GitRepository:
    full_path = os.path.realpath(path)

    if os.path.isdir(os.path.join(full_path, ".git")):
        return GitRepository(full_path)

    parent = os.path.realpath(os.path.join(full_path, ".."))
    if parent == full_path:
        raise Exception("No git repository found")

    return repository_find(parent)


def repository_path(repository: GitRepository, *path: str) -> str:
    return os.path.join(repository.gitdir, *path)


def repository_dir(repository: GitRepository, *path: str, mkdir=False) -> str:
    full_path = repository_path(repository, *path)

    if os.path.exists(full_path):
        if os.path.isdir(full_path):
            return full_path
        else:
            raise Exception(f"Not a directory: {path}")

    if mkdir:
        try:
            os.makedirs(full_path)
        except OSError as e:
            raise RuntimeError(f"Failed to create directory {full_path}: {e}")
    raise FileNotFoundError(f"Directory does not exist: {full_path}")


def repository_file(repository: GitRepository, *path: str, mkdir=False) -> str:
    repository_dir(repository, *path[:-1], mkdir=mkdir)
    return repository_path(repository, *path)


def repository_create(path: str) -> GitRepository:
    repository = GitRepository(path, True)

    if os.path.exists(repository.worktree):
        if not os.path.isdir(repository.worktree):
            raise NotADirectoryError(f"{path} is not a directory")
        if os.path.exists(repository.gitdir) and os.listdir(repository.gitdir):
            raise FileExistsError(f"{path} is not empty")
    else:
        os.makedirs(repository.worktree, exist_ok=True)

    ensure_dirs(repository, ["branches", "objects", "refs/tags", "refs/heads"])
    ensure_files(
        repository,
        {
            "description": "Unnamed repository",
            "HEAD": "ref: refs/heads/main\n",
        },
    )
    from config import write_config

    write_config(repository)

    return repository


def ensure_dirs(repository: GitRepository, dirs: list[str]):
    for dir_path in dirs:
        try:
            repository_dir(repository, dir_path, mkdir=True)
        except Exception as e:
            raise RuntimeError(f"Failed to create directory {dir_path}: {e}")


def ensure_files(repository: GitRepository, files: dict[str, Optional[str]]):
    for filename, content in files.items():
        try:
            path = repository_file(repository, filename, mkdir=True)
        except Exception as e:
            raise RuntimeError(f"Failed to create file {filename}: {e}")
        with open(path, "w") as f:
            if content is not None:
                f.write(content)
