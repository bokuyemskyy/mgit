from __future__ import annotations

import os
from configparser import ConfigParser
from typing import Optional
import zlib
import hashlib
import re
from app.objects import GitBlob, GitCommit, GitObject, GitTag, GitTree
from typing import Dict, Union
from .config import default_config

RefTree = Dict[str, Union[str, "RefTree"]]


class GitRepository:
    def __init__(self, path: str, create=True) -> None:
        self.worktree: str = os.path.realpath(path)
        self.gitdir: str = os.path.join(self.worktree, ".git")

        if os.path.exists(self.worktree):
            if not os.path.isdir(self.worktree):
                raise NotADirectoryError(f"{self.worktree} is not a directory")
        else:
            os.makedirs(self.worktree, exist_ok=True)

        if create:
            os.makedirs(self.gitdir, exist_ok=True)

            for dir_name in ["branches", "objects", "refs/tags", "refs/heads"]:
                self.dir_ensure(dir_name)

            files_to_create = {
                "description": "Unnamed repository\n",
                "HEAD": "ref: refs/heads/main\n",
            }

            for filename, content in files_to_create.items():
                if not self.file_exists(filename):
                    self.file_ensure(filename, content=content)

        config_path = self.resolve_path("config")

        if os.path.isfile(config_path):
            self.config: ConfigParser = ConfigParser(strict=False)
            self.config.read(config_path)
        else:
            with open(config_path, "w", encoding="utf-8") as config_file:
                self.config: ConfigParser = default_config()
                self.config.write(config_file)

    @classmethod
    def find(cls, path: str = ".", max_depth: int = 64) -> GitRepository:
        full_path = os.path.realpath(path)
        depth = 0

        while True:
            if depth >= max_depth:
                raise FileNotFoundError(
                    f"No git repository found within {max_depth} levels"
                )

            gitdir_path = os.path.join(full_path, ".git")
            if os.path.isdir(gitdir_path):
                return cls(full_path, create=False)

            parent = os.path.realpath(os.path.join(full_path, ".."))
            if parent == full_path:
                raise FileNotFoundError("No git repository found")

            full_path = parent
            depth += 1

    @classmethod
    def create(cls, path: str) -> GitRepository:
        return cls(path, create=True)

    def resolve_path(self, *subpath: str) -> str:
        return os.path.join(self.gitdir, *subpath)

    def dir_exists(self, *subpath: str) -> bool:
        return os.path.isdir(self.resolve_path(*subpath))

    def dir_ensure(self, *subpath: str) -> str:
        path = self.resolve_path(*subpath)
        os.makedirs(path, exist_ok=True)
        if not os.path.isdir(path):
            raise NotADirectoryError(f"Failed to create directory: {path}")
        return path

    def dir_require(self, *subpath: str) -> str:
        path = self.resolve_path(*subpath)

        if not os.path.isdir(path):
            raise NotADirectoryError(f"Required dir not found: {path}")
        return path

    def file_exists(self, *subpath: str) -> bool:
        return os.path.isfile(self.resolve_path(*subpath))

    def file_ensure(self, *subpath: str, content: Optional[str] = None) -> str:
        self.dir_ensure(*subpath[:-1])

        path = self.resolve_path(*subpath)

        if os.path.exists(path) and not os.path.isfile(path):
            raise IsADirectoryError(f"Is a directory: {path}")

        with open(path, "w") as f:
            if content is not None:
                f.write(content)

        return path

    def file_require(self, *subpath: str) -> str:
        path = self.resolve_path(*subpath)

        if not os.path.isfile(path):
            raise FileNotFoundError(f"Required file not found: {path}")
        return path

    def object_file(self, sha: str) -> str:
        path = self.file_require("objects", sha[:2], sha[2:])
        return path

    def object_read(self, sha: str) -> GitObject:
        path = self.file_require("objects", sha[:2], sha[2:])

        with open(path, "rb") as f:
            raw = zlib.decompress(f.read())

            fmt_sep = raw.find(b" ")
            if fmt_sep < 0:
                raise ValueError("Missing type separator")
            fmt = raw[:fmt_sep]

            size_sep = raw.find(b"\x00", fmt_sep)
            if size_sep < 0:
                raise ValueError("Missing size separator")

            size = int(raw[fmt_sep + 1 : size_sep].decode("ascii"))
            if size != len(raw) - size_sep - 1:
                raise ValueError(f"Malformed object {sha}: bad length")

            match fmt:
                case b"commit":
                    object_class = GitCommit
                case b"tree":
                    object_class = GitTree
                case b"tag":
                    object_class = GitTag
                case b"blob":
                    object_class = GitBlob
                case _:
                    raise ValueError(f"Unknown object type: {fmt.decode('ascii')}")

            return object_class.deserialize(raw[size_sep + 1 :])

    def object_find(
        self,
        name: str,
        fmt: Optional[bytes] = None,
        follow=True,
    ) -> str:
        sha = self.object_resolve(name)

        if len(sha) == 0:
            raise ValueError("No object found")

        if len(sha) > 1:
            raise ValueError(f"Ambiguous reference {name}:\n - {'\n - '.join(sha)}")

        sha = sha[0]

        if not fmt:
            return sha

        while True:
            obj = self.object_read(sha)

            if obj.fmt == fmt:
                return sha

            if not follow:
                raise FileNotFoundError("The object cannot be found")

            if isinstance(obj, GitTag):
                if not isinstance(obj.kvlm[b"object"], bytes):
                    raise ValueError("Invalid KVLM")
                sha = obj.kvlm[b"object"].decode("ascii")
            elif isinstance(obj, GitCommit) and fmt == b"tree":
                if not isinstance(obj.kvlm[b"tree"], bytes):
                    raise ValueError("Invalid KVLM")
                sha = obj.kvlm[b"tree"].decode("ascii")
            else:
                raise FileNotFoundError("The object cannot be found")

    @staticmethod
    def object_hash(raw: bytes) -> str:
        return hashlib.sha1(raw).hexdigest()

    @staticmethod
    def object_raw(obj: GitObject) -> bytes:
        data = obj.serialize()
        return obj.fmt + b" " + str(len(data)).encode() + b"\x00" + data

    def object_write(self, obj: GitObject) -> str:
        raw = self.object_raw(obj)
        sha = self.object_hash(raw)

        self.dir_ensure("objects", sha[:2])
        path = self.resolve_path("objects", sha[:2], sha[2:])

        with open(path, "wb") as object_file:
            object_file.write(zlib.compress(raw))

        return sha

    def object_resolve(self, name: str) -> list[str]:
        candidates = []

        if not name.strip():
            return candidates

        if name == "HEAD":
            candidates.append(self.ref_resolve("HEAD"))
            return candidates

        hash_re = re.compile(r"^[0-9A-Fa-f]{4,40}$")
        if hash_re.match(name):
            name = name.lower()
            prefix = name[:2]
            remainder = name[2:]
            if self.dir_exists("objects", prefix):
                for file in os.listdir(self.resolve_path("objects", prefix)):
                    if file.startswith(remainder):
                        candidates.append(prefix + file)

        try:
            candidates.append(self.ref_resolve("refs/tags/" + name))
        except FileNotFoundError:
            pass
        try:
            candidates.append(self.ref_resolve("refs/heads/" + name))
        except FileNotFoundError:
            pass
        try:
            candidates.append(self.ref_resolve("refs/remotes/" + name))
        except FileNotFoundError:
            pass

        return candidates

    def ref_resolve(self, ref: str, max_depth: int = 64) -> str:
        depth = 0
        while True:
            if depth >= max_depth:
                raise RecursionError(
                    f"Too many symbolic ref indirections (>{max_depth})"
                )

            path = self.file_require(ref)

            with open(path, "r") as f:
                data = f.read().strip()

            if data.startswith("ref: "):
                ref = data[5:]
                depth += 1
                continue

            return data

    def ref_list(self, path: str = "refs") -> RefTree:
        dir = self.dir_require(path)
        result: RefTree = {}

        for entry in sorted(os.listdir(dir)):
            full_path = os.path.join(dir, entry)
            name = os.path.join(path, entry)

            if os.path.isdir(full_path):
                result[entry] = self.ref_list(name)
            else:
                result[entry] = self.ref_resolve(name)

        return result

    def ref_create(self, *subpath: str, sha: str) -> str:
        return self.file_ensure(*subpath, content=sha + "\n")
