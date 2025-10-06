import os
import zlib
import hashlib
import re
from typing import Optional
from app.objects import GitBlob, GitCommit, GitObject, GitTag, GitTree


class GitObjects:
    def __init__(self, fs):
        self.fs = fs

    def file(self, sha: str) -> str:
        return self.fs.file_require("objects", sha[:2], sha[2:])

    def read(self, sha: str) -> GitObject:
        path = self.file(sha)
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

    def find(
        self,
        name: str,
        fmt: Optional[bytes] = None,
        follow=True,
    ) -> str:
        sha_list = self.resolve(name)

        if not sha_list:
            raise ValueError("No object found")

        if len(sha_list) > 1:
            raise ValueError(
                f"Ambiguous reference {name}:\n - {'\n - '.join(sha_list)}"
            )

        sha = sha_list[0]

        if fmt is None:
            return sha
        while True:
            obj = self.read(sha)
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
    def hash(raw: bytes) -> str:
        return hashlib.sha1(raw).hexdigest()

    @staticmethod
    def raw(obj: GitObject) -> bytes:
        data = obj.serialize()
        return obj.fmt + b" " + str(len(data)).encode() + b"\x00" + data

    def write(self, obj: GitObject) -> str:
        raw = self.raw(obj)
        sha = self.hash(raw)
        self.fs.dir_ensure("objects", sha[:2])
        path = self.fs.resolve_path("objects", sha[:2], sha[2:])
        with open(path, "wb") as object_file:
            object_file.write(zlib.compress(raw))
        return sha

    def resolve(self, name: str) -> list[str]:
        candidates = []
        if not name.strip():
            return candidates
        if name == "HEAD":
            from .references import GitReferences

            refs = GitReferences(self.fs)
            candidates.append(refs.resolve("HEAD"))
            return candidates
        hash_re = re.compile(r"^[0-9A-Fa-f]{4,40}$")
        if hash_re.match(name):
            name = name.lower()
            prefix = name[:2]
            remainder = name[2:]
            if self.fs.dir_exists("objects", prefix):
                for file in os.listdir(self.fs.resolve_path("objects", prefix)):
                    if file.startswith(remainder):
                        candidates.append(prefix + file)
        from .references import GitReferences

        refs = GitReferences(self.fs)
        for ref in ["refs/tags/" + name, "refs/heads/" + name, "refs/remotes/" + name]:
            try:
                candidates.append(refs.resolve(ref))
            except FileNotFoundError:
                continue
        return candidates
