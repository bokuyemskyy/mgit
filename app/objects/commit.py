from __future__ import annotations

from typing import Optional
from app.repository.repository import GitRepository
from .object import GitObject


class GitCommit(GitObject):
    fmt = b"commit"

    kvlm: dict[Optional[bytes], list[bytes]]

    def initialize(self):
        self.kvlm = {}

    def serialize(self, repository: GitRepository | None = None) -> bytes:
        return kvlm_serialize(self.kvlm)

    @classmethod
    def deserialize(cls, data: bytes) -> GitCommit:
        instance = cls()
        instance.kvlm = kvlm_deserialize(data)
        return instance


def kvlm_deserialize(raw: bytes, kvlm: Optional[dict] = None) -> dict:
    size = len(raw)

    if kvlm is None:
        kvlm = {}

    pos = 0
    while pos < size:
        space = raw.find(b" ", pos)
        newline = raw.find(b"\n", pos)

        if (space < 0) or (newline < space):
            if newline != pos:
                raise ValueError(f"Expected blank line at position {pos}")
            kvlm[None][0] = raw[pos + 1:]
            return kvlm

        key = raw[pos:space]

        end = pos
        while True:
            end = raw.find(b"\n", end + 1)
            if end < 0 or raw[end + 1] != ord(" "):
                break

        value = raw[space + 1:end].replace(b"\n ", b"\n")

        if key in kvlm:
            if isinstance(kvlm[key], list):
                kvlm[key].append(value)
            else:
                kvlm[key] = [kvlm[key], value]
        else:
            kvlm[key] = [value]

        pos = end + 1

    return kvlm


def kvlm_serialize(kvlm: dict) -> bytes:
    result = b""

    for key, values in kvlm.items():
        if key is None:
            continue

        if not isinstance(values, list):
            values = [values]

        for value in values:
            result += key + b" " + value.replace(b"\n", b"\n ") + b"\n"

    if None in kvlm:
        result += b"\n" + kvlm[None][0]

    return result
