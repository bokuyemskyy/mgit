import os
import zlib
import hashlib

from typing import BinaryIO, Optional

from app.repository import GitRepository, repository_file
from app.objects import GitObject, GitBlob, GitCommit, GitTag, GitTree


def object_read(repository: GitRepository, sha: str) -> GitObject:
    full_path = repository_file(repository, "objects", sha[:2], sha[2:])

    if not os.path.isfile(full_path):
        raise FileNotFoundError(f"Not a file: {full_path}")

    with open(full_path, "rb") as object_file:
        raw = zlib.decompress(object_file.read())

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
    repository: GitRepository,
    name: str,
    fmt: Optional[str] = None,
    follow=True,
) -> str:
    return name


def object_hash(raw: bytes) -> str:
    return hashlib.sha1(raw).hexdigest()


def object_raw(object: GitObject) -> bytes:
    data = object.serialize()
    return object.fmt + b" " + str(len(data)).encode() + b"\x00" + data


def object_write(object: GitObject, repository: GitRepository) -> str:
    raw = object_raw(object)
    sha = object_hash(raw)

    full_path = repository_file(repository, "objects", sha[:2], sha[2:], mkdir=True)
    if not os.path.exists(full_path):
        with open(full_path, "wb") as object_file:
            object_file.write(zlib.compress(raw))

    return sha
