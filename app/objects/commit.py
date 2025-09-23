from app.repository.repository import GitRepository
from .object import GitObject


class GitCommit(GitObject):
    format = b"commit"
    kvlm: dict

    def initialize(self):
        self.kvlm = dict()

    def serialize(self, repository: GitRepository | None = None) -> bytes:
        return kvlm_serialize(self.kvlm)

    def deserialize(self, raw: bytes) -> None:
        self.kvlm = kvlm_deserialize(raw)


def kvlm_deserialize(raw, kvlm=None):
    size = len(raw)

    if kvlm is None:
        kvlm = dict()

    pos = 0
    while pos < size:
        space = raw.find(b" ", pos)
        newline = raw.find(b"\n", pos)

        if (space < 0) or (newline < space):
            if newline != pos:
                raise ValueError(f"Expected blank line at position {pos}")
            kvlm[None] = raw[pos + 1 :]
            return kvlm

        key = raw[pos:space]

        end = pos

        while True:
            end = raw.find(b"\n", end + 1)
            if raw[end + 1] != ord(" "):
                break

        value = raw[space + 1 : end].replace(b"\n ", b"\n")

        if key in kvlm:
            kvlm[key].append(value)
        else:
            kvlm[key] = [value]

        pos = end + 1

    return kvlm


def kvlm_serialize(kvlm):
    result = b""

    for key in kvlm.keys():
        if key == None:
            continue

        values = kvlm[key]

        for value in values:
            result += key + b" " + value.replace(b"\n", b"\n ") + b"\n"

    result += b"\n" + kvlm[None]

    return result
