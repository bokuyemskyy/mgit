from __future__ import annotations

import os
from fnmatch import fnmatch
from typing import Dict, List, Optional, Tuple

from app.objects import GitBlob
from app.repository import GitIndex, GitRepository

Rule = Tuple[str, bool]


class GitIgnore:
    def __init__(self, absolute: List[Rule], scoped: Dict[str, List[Rule]]):
        self.absolute = absolute
        self.scoped = scoped

    @staticmethod
    def _check_rules(rules: List[Rule], path: str) -> Optional[bool]:
        result = None
        for pattern, is_ignored in rules:
            if fnmatch(path, pattern):
                result = is_ignored
        return result

    def check_ignore(self, path: str) -> bool:
        if os.path.isabs(path):
            raise ValueError(
                "The path should be relative to the root of the repository"
            )

        parent = os.path.dirname(path)
        while True:
            if parent in self.scoped:
                result = self._check_rules(self.scoped[parent], path)
                if result is not None:
                    return result
            if not parent:
                break
            parent = os.path.dirname(parent)

        result = self._check_rules(self.absolute, path)
        return result if result is not None else False

    @classmethod
    def read(cls, repo: GitRepository) -> GitIgnore:
        absolute_rules: List[Rule] = []
        scoped_rules: Dict[str, List[Rule]] = {}

        try:
            content = repo.fs.file_read("info/exclude", root="git", binary=False)
            absolute_rules.extend(cls._parse_lines(content.splitlines()))
        except FileNotFoundError:
            pass

        config_home = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
        global_file = os.path.join(config_home, "git/ignore")
        if os.path.exists(global_file):
            with open(global_file, "r") as f:
                absolute_rules.extend(cls._parse_lines(f.readlines()))

        index = GitIndex.read(repo)
        for entry in index.entries:
            if entry.name == ".gitignore" or entry.name.endswith("/.gitignore"):
                dir_name = os.path.dirname(entry.name)
                blob = repo.objects.read(entry.sha)
                if isinstance(blob, GitBlob):
                    content = blob.data.decode("utf8")
                    scoped_rules[dir_name] = cls._parse_lines(content.splitlines())

        return cls(absolute=absolute_rules, scoped=scoped_rules)

    @classmethod
    def _parse_lines(cls, lines: List[str]) -> List[Rule]:
        rules = []
        for line in lines:
            rule = cls._parse_line(line)
            if rule:
                rules.append(rule)
        return rules

    @staticmethod
    def _parse_line(line: str) -> Optional[Rule]:
        line = line.strip()
        if not line or line.startswith("#"):
            return None

        # Handle negation
        if line.startswith("!"):
            return (line[1:], False)
        # Handle escaping
        if line.startswith("\\"):
            return (line[1:], True)

        return (line, True)
