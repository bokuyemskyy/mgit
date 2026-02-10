from __future__ import annotations
import os
from typing import Dict, List, Optional, Tuple
from app.objects import GitBlob
from app.repository import GitRepository, GitIndex, GitObjects
from app.cli import logger
from fnmatch import fnmatch


Rule = Tuple[str, bool]


class GitIgnore:
    def __init__(self, absolute: List, scoped: Dict):
        self.absolute = absolute
        self.scoped = scoped

    @classmethod
    def check_ignore_one(cls, rules: List[Rule], path: str):
        result = None
        for pattern, value in rules:
            if fnmatch(path, pattern):
                result = value
        return result

    @classmethod
    def check_ignore_scoped(cls, rules: List[Rule], path: str):
        parent = os.path.dirname(path)
        while True:
            if parent in rules:
                result = GitIgnore.check_ignore_one(rules[parent], path)
                if result is not None:
                    return result
            if parent == "":
                break
            parent = os.path.dirname(parent)
        return None

    @classmethod
    def check_ignore_absolute(cls, rules, path):
        for rule in rules:
            result = GitIgnore.check_ignore_one(rule, path)
            if result is not None:
                return result
        return False

    def check_ignore(self, path):
        if os.path.isabs(path):
            raise Exception("The path should be relative to the root of the repository")

        result = GitIgnore.check_ignore_scoped(self.scoped, path)
        if result is not None:
            return result

        return GitIgnore.check_ignore_absolute(self.absolute, path)

    @classmethod
    def read(cls, repo: GitRepository) -> GitIgnore:
        result = GitIgnore(absolute=list(), scoped=dict())

        try:
            content = repo.fs.file_read("info/exclude", root="git", binary=False)
            result.absolute.append(GitIgnore._parse_lines(content.splitlines()))
        except FileNotFoundError:
            pass

        if "XDG_CONFIG_HOME" in os.environ:
            config_home = os.environ["XDG_CONFIG_HOME"]
        else:
            config_home = os.path.expanduser("~/.config")
        global_file = os.path.join(config_home, "git/ignore")

        if os.path.exists(global_file):
            with open(global_file, "r") as f:
                result.absolute.append(GitIgnore._parse_lines(f.readlines()))

        index = GitIndex.read(repo)

        # check in practice
        for entry in index.entries:
            if entry.name == ".gitignore" or entry.name.endswith("/.gitignore"):
                dir_name = os.path.dirname(entry.name)
                blob = repo.objects.read(entry.sha)
                assert isinstance(blob, GitBlob)
                content = blob.data.decode("utf8")
                result.scoped[dir_name] = GitIgnore._parse_lines(content.splitlines())

        return result

    @classmethod
    def _parse_lines(cls, lines: List[str]) -> List[Rule]:
        result = list()

        for line in lines:
            parsed = GitIgnore._parse_line(line)
            if parsed:
                result.append(parsed)

        return result

    @classmethod
    def _parse_line(cls, line: str) -> Optional[Rule]:
        line = line.strip()

        if not line or line.startswith("#"):
            return None
        elif line[0] == "!":
            return (line[1:], False)
        elif line[0] == "\\":
            return (line[1:], True)
        else:
            return (line, True)
