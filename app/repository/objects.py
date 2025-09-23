import os
import zlib
import hashlib

from typing import BinaryIO, Optional

from .repository import GitRepository, repository_file
from app.objects import GitObject, GitBlob, GitCommit, GitTag, GitTree


def object_read(repository: GitRepository, sha: str) -> GitObject:
    full_path = repository_file(repository, "objects", sha[:2], sha[2:])

    if not os.path.isfile(full_path):
        raise FileNotFoundError(f"Not a file: {full_path}")

    with open(full_path, "rb") as object_file:
        raw = zlib.decompress(object_file.read())

        format_sep = raw.find(b" ")
        if format_sep < 0:
            raise ValueError("Missing type separator")
        object_format = raw[:format_sep]

        size_sep = raw.find(b"\x00", format_sep)
        if size_sep < 0:
            raise ValueError("Missing size separator")

        object_size = int(raw[format_sep + 1 : size_sep].decode("ascii"))
        if object_size != len(raw) - size_sep - 1:
            raise ValueError(f"Malformed object {sha}: bad length")

        match object_format:
            case b"commit":
                constructor = GitCommit
            case b"tree":
                constructor = GitTree
            case b"tag":
                constructor = GitTag
            case b"blob":
                constructor = GitBlob
            case _:
                raise ValueError(
                    f"Unknown object type: {object_format.decode('ascii')}"
                )

        return constructor(raw[size_sep + 1 :])


def object_write(object: GitObject, repository: Optional[GitRepository] = None) -> str:
    data = object.serialize()
    raw = object.format + b" " + str(len(data)).encode() + b"\x00" + data
    sha = hashlib.sha1(raw).hexdigest()

    if repository:
        full_path = repository_file(repository, "objects", sha[:2], sha[2:], mkdir=True)

        if not os.path.exists(full_path):
            with open(full_path, "wb") as object_file:
                object_file.write(zlib.compress(raw))

    return sha


def object_find(
    repository: GitRepository, sha: str, format: Optional[str] = None, follow=True
) -> str:
    return sha


def object_hash(
    file: BinaryIO, object_format: bytes, repository: Optional[GitRepository] = None
) -> str:
    raw = file.read()

    match object_format:
        case b"commit":
            constructor = GitCommit
        case b"tree":
            constructor = GitTree
        case b"tag":
            constructor = GitTag
        case b"blob":
            constructor = GitBlob
        case _:
            raise ValueError(f"Unknown object type: {object_format.decode('ascii')}")

    return object_write(constructor(raw), repository)
