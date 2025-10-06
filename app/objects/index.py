from __future__ import annotations
import os
from typing import Tuple, Optional, List
from app.repository import GitRepository
from math import ceil
from app.cli import logger

Timestamp = Tuple[int, int]


class GitIndexEntry:
    def __init__(
        self,
        ctime: Optional[Timestamp] = None,
        mtime: Optional[Timestamp] = None,
        dev: Optional[int] = None,
        ino: Optional[int] = None,
        mode_type: Optional[int] = None,
        mode_perms: Optional[int] = None,
        uid: Optional[int] = None,
        gid: Optional[int] = None,
        fsize: Optional[int] = None,
        sha: Optional[str] = None,
        assume_valid: Optional[bool] = None,
        stage: Optional[int] = None,
        name: Optional[str] = None,
    ):
        self.ctime = ctime
        self.mtime = mtime
        self.dev = dev
        self.ino = ino
        self.mode_type = mode_type
        self.mode_perms = mode_perms
        self.uid = uid
        self.gid = gid
        self.fsize = fsize
        self.sha = sha
        self.assume_valid = assume_valid
        self.stage = stage
        self.name = name


class GitIndex:
    def __init__(self, version: int = 2, entries: Optional[List[GitIndexEntry]] = None):
        if entries is None:
            entries = list()

        self.version = version
        self.entries = entries

    @classmethod
    def read(cls, repo: GitRepository) -> GitIndex:
        if not repo.fs.file_exists("index"):
            return cls()

        raw: bytes = repo.fs.file_read("index", binary=True)

        header = raw[:12]
        signature = header[:4]
        if signature != b"DIRC":
            raise ValueError("Invalid index file signature")

        version = int.from_bytes(header[4:8], "big")
        if version != 2:
            raise ValueError("mgit only supports index file version 2")

        count = int.from_bytes(header[8:12], "big")

        entries: List[GitIndexEntry] = []
        content = raw[12:]
        idx = 0

        for i in range(0, count):
            ctime_s = int.from_bytes(content[idx : idx + 4], "big")
            ctime_ns = int.from_bytes(content[idx + 4 : idx + 8], "big")

            mtime_s = int.from_bytes(content[idx + 8 : idx + 12], "big")
            mtime_ns = int.from_bytes(content[idx + 12 : idx + 16], "big")

            dev = int.from_bytes(content[idx + 16 : idx + 20], "big")
            ino = int.from_bytes(content[idx + 20 : idx + 24], "big")

            unused = int.from_bytes(content[idx + 24 : idx + 26], "big")
            if unused != 0:
                logger.warning("Index entry {i} has non-zero unused field")

            mode = int.from_bytes(content[idx + 26 : idx + 30], "big")
            mode_type = mode >> 12
            if mode_type not in [0o10, 0o12, 0o16]:
                raise ValueError(f"Unknown index entry mode type: {mode_type}")

            mode_perms = mode & 0o0000777

            uid = int.from_bytes(content[idx + 30 : idx + 34], "big")
            gid = int.from_bytes(content[idx + 34 : idx + 38], "big")
            fsize = int.from_bytes(content[idx + 38 : idx + 42], "big")

            sha = format(int.from_bytes(content[idx + 42 : idx + 62], "big"), "040x")

            flags = int.from_bytes(content[idx + 62 : idx + 64], "big")
            assume_valid = (flags & 0b1000000000000000) != 0
            extended = (flags & 0b0100000000000000) != 0

            if extended:
                logger.warning("Extended flags are not supported")

            stage = (flags & 0b0011000000000000) >> 12
            name_length = flags & 0b0000111111111111

            idx += 64

            if name_length < 0xFFF:
                raw_name = content[idx : idx + name_length]
                idx += name_length

                if content[idx] != 0x00:
                    raise ValueError("Index entry name not null-terminated.")
                idx += 1
            else:
                null_idx = content.find(b"\x00", idx + name_length)
                if null_idx == -1:
                    raise ValueError("Long index entry name not null-terminated")
                raw_name = content[idx:null_idx]
                idx = null_idx + 1

            name = raw_name.decode("utf8")

            padding_needed = 8 * ceil(idx / 8) - idx
            idx += padding_needed

            entries.append(
                GitIndexEntry(
                    ctime=(ctime_s, ctime_ns),
                    mtime=(mtime_s, mtime_ns),
                    dev=dev,
                    ino=ino,
                    mode_type=mode_type,
                    mode_perms=mode_perms,
                    uid=uid,
                    gid=gid,
                    fsize=fsize,
                    sha=sha,
                    assume_valid=assume_valid,
                    stage=stage,
                    name=name,
                )
            )

        return cls(version=version, entries=entries)
