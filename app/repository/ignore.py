from __future__ import annotations
from typing import Tuple
from app.repository import GitRepository
from app.cli import logger

Timestamp = Tuple[int, int]


class GitIgnore:
    def __init__(self, repo: GitRepository, absolute: bool, scoped: bool):
        self.repo = repo
        self.absolute = absolute
        self.scoped = scoped

    def is_ignored(self, path: str) -> bool:
        for pattern in self.patterns:
            if fnmatch.fnmatch(path, pattern):
                return True
        return False

    @classmethod
    def read(cls, repo: GitRepository) -> GitIgnore:
        if not repo.fs.file_exists(".gitignore"):
            return cls([])

        raw = repo.fs.file_read(".gitignore", binary=False)
        patterns = [line.strip() for line in raw.splitlines() if line.strip()]
        return cls(patterns)

    @classmethod
    def parse_line(line: str) -> str:
        line = line.strip()

        if not line or line.startswith("#"):
            return Exception("String is empty")
