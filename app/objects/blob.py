from __future__ import annotations

from .object import GitObject


class GitBlob(GitObject):
    fmt = b"blob"

    data: bytes

    def initialize(self):
        self.data = b""

    def serialize(self) -> bytes:
        return self.data

    @classmethod
    def deserialize(cls, data: bytes) -> GitBlob:
        instance = cls()
        instance.data = data
        return instance
