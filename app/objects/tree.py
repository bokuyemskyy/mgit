from __future__ import annotations

from .object import GitObject


class GitTree(GitObject):
    fmt = b"tree"

    items: list[GitTreeLeaf]

    def initialize(self):
        self.items = list()

    def serialize(self) -> bytes:
        result = b""

        self.items.sort(key=lambda leaf: leaf.sort_key())
        for item in self.items:
            result += item.serialize()

        return result

    @classmethod
    def deserialize(cls, data: bytes) -> GitTree:
        instance = cls()

        pos = 0
        size = len(data)

        while pos < size:
            node, consumed = GitTreeLeaf.deserialize(data[pos:])
            pos += consumed
            instance.items.append(node)

        return instance


class GitTreeLeaf:
    def __init__(self, mode: bytes, path: str, sha: str):
        self.mode = mode
        self.path = path
        self.sha = sha

    def serialize(self) -> bytes:
        result = self.mode + b" " + self.path.encode() + b"\x00"
        sha_int = int(self.sha, 16)
        result += sha_int.to_bytes(20, "big")
        return result

    @classmethod
    def deserialize(cls, raw: bytes) -> tuple[GitTreeLeaf, int]:
        mode_separator = raw.find(b" ")
        if mode_separator not in (5, 6):
            raise ValueError("Missing or invalid mode separator")

        mode = raw[:mode_separator]
        if len(mode) == 5:
            mode = b"0" + mode

        path_separator = raw.find(b"\x00", mode_separator)
        if path_separator < 0:
            raise ValueError("Missing path separator")

        path = raw[mode_separator + 1 : path_separator].decode("utf-8")

        SHA_SIZE = 20

        if len(raw) < path_separator + SHA_SIZE + 1:
            raise ValueError("Raw data too short for SHA")
        raw_sha = int.from_bytes(
            raw[path_separator + 1 : path_separator + 1 + SHA_SIZE], "big"
        )
        sha = format(raw_sha, "040x")

        consumed_length = path_separator + 1 + SHA_SIZE

        return cls(mode, path, sha), consumed_length

    def sort_key(self) -> str:
        if self.mode.startswith(b"10"):
            return self.path
        return self.path + "/"
