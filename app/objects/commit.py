from __future__ import annotations

from typing import Dict, List, Optional

from .object import GitObject


class KeyValueListWithMessage:
    def __init__(self) -> None:
        self._data: Dict[bytes, List[bytes]] = {}
        self._message: bytes = b""

    def set(self, key: bytes, value: bytes) -> None:
        self._data[key] = [value]

    def append(self, key: bytes, value: bytes) -> None:
        if key not in self._data:
            self._data[key] = []
        self._data[key].append(value)

    def get(self, key: bytes) -> List[bytes]:
        if key not in self._data:
            return []
        return self._data[key]

    def get_one(self, key: bytes) -> Optional[bytes]:
        values = self._data.get(key)
        if values:
            return values[0]
        return None

    def set_message(self, value: bytes) -> None:
        self._message = value

    def get_message(self) -> bytes:
        if self._message == b"":
            raise ValueError("no commit message")
        return self._message

    @classmethod
    def deserialize(cls, data: bytes) -> KeyValueListWithMessage:
        kvlm = KeyValueListWithMessage()

        size = len(data)

        pos = 0
        while pos < size:
            space = data.find(b" ", pos)
            newline = data.find(b"\n", pos)

            if (space < 0) or (newline < space):
                if newline != pos:
                    raise ValueError(f"Expected blank line at position {pos}")
                kvlm.set_message(data[pos + 1 :])
                return kvlm
            key = data[pos:space]

            end = pos
            while True:
                end = data.find(b"\n", end + 1)
                if end < 0 or data[end + 1] != ord(" "):
                    break

            value = data[space + 1 : end].replace(b"\n ", b"\n")

            kvlm.append(key, value)

            pos = end + 1

        return kvlm

    def serialize(self) -> bytes:
        result = b""

        for key, values in self._data.items():
            for value in values:
                result += key + b" " + value.replace(b"\n", b"\n ") + b"\n"

        result += b"\n" + self.get_message()

        return result


class GitCommit(GitObject):
    fmt = b"commit"

    kvlm: KeyValueListWithMessage

    def initialize(self):
        self.kvlm = KeyValueListWithMessage()

    def serialize(self) -> bytes:
        return self.kvlm.serialize()

    @classmethod
    def deserialize(cls, data: bytes) -> GitCommit:
        instance = cls()
        instance.kvlm = KeyValueListWithMessage.deserialize(data)
        return instance
