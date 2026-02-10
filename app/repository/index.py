from __future__ import annotations
from typing import Tuple, Optional, List
from app.repository import GitRepository
from math import ceil
from app.cli import logger

Timestamp = Tuple[int, int]


class GitIndexEntry:
    def __init__(
        self,
        ctime: Timestamp,
        mtime: Timestamp,
        dev: int,
        ino: int,
        mode_type: int,
        mode_perms: int,
        uid: int,
        gid: int,
        fsize: int,
        sha: str,
        assume_valid: bool,
        stage: int,
        name: str,
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
        self.version = version
        self.entries = entries if entries is not None else []

    @classmethod
    def read(cls, repo: GitRepository) -> GitIndex:
        if not repo.fs.file_exists("index"):
            return cls()

        raw: bytes = repo.fs.file_read("index", binary=True)
        header = raw[:12]

        if header[:4] != b"DIRC":
            raise ValueError("Invalid index file signature")

        version = int.from_bytes(header[4:8], "big")
        if version != 2:
            raise ValueError("mgit only supports index file version 2")

        count = int.from_bytes(header[8:12], "big")
        entries: List[GitIndexEntry] = []
        content = raw[12:]
        idx = 0

        for i in range(count):
            ctime_s = int.from_bytes(content[idx : idx + 4], "big")
            ctime_ns = int.from_bytes(content[idx + 4 : idx + 8], "big")
            mtime_s = int.from_bytes(content[idx + 8 : idx + 12], "big")
            mtime_ns = int.from_bytes(content[idx + 12 : idx + 16], "big")
            dev = int.from_bytes(content[idx + 16 : idx + 20], "big")
            ino = int.from_bytes(content[idx + 20 : idx + 24], "big")
            unused = int.from_bytes(content[idx + 24 : idx + 26], "big")
            if unused != 0:
                logger.warning(f"Index entry {i} has non-zero unused field")

            mode = int.from_bytes(content[idx + 26 : idx + 28], "big")
            mode_type = mode >> 12
            if mode_type not in [0b1000, 0b1010, 0b1110]:
                raise ValueError(f"Unknown index entry mode type: {mode_type}")
            mode_perms = mode & 0o777

            uid = int.from_bytes(content[idx + 28 : idx + 32], "big")
            gid = int.from_bytes(content[idx + 32 : idx + 36], "big")
            fsize = int.from_bytes(content[idx + 36 : idx + 40], "big")
            sha = format(int.from_bytes(content[idx + 40 : idx + 60], "big"), "040x")
            flags = int.from_bytes(content[idx + 60 : idx + 62], "big")

            assume_valid = (flags & 0b1000000000000000) != 0
            extended = (flags & 0b0100000000000000) != 0
            if extended:
                logger.warning(f"Index entry {i} has unsupported extended flags")
            stage = (flags & 0b0011000000000000) >> 12
            name_length = flags & 0b0000111111111111

            idx += 62

            if name_length < 0xFFF:
                raw_name = content[idx : idx + name_length]
                idx += name_length
                if content[idx] != 0x00:
                    raise ValueError("Index entry name not null-terminated")
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

    # to verify
    def write(self, repo: GitRepository):
        content = bytearray()

        content += b"DIRC"
        content += self.version.to_bytes(4, "big")
        content += len(self.entries).to_bytes(4, "big")

        idx = 0

        for entry in self.entries:
            content += entry.ctime[0].to_bytes(4, "big")
            content += entry.ctime[1].to_bytes(4, "big")
            content += entry.mtime[0].to_bytes(4, "big")
            content += entry.mtime[1].to_bytes(4, "big")
            content += entry.dev.to_bytes(4, "big")
            content += entry.ino.to_bytes(4, "big")

            mode = (entry.mode_type << 12) | entry.mode_perms
            content += mode.to_bytes(4, "big")

            content += entry.uid.to_bytes(4, "big")
            content += entry.gid.to_bytes(4, "big")

            content += entry.fsize.to_bytes(4, "big")
            content += int(entry.sha, 16).to_bytes(20, "big")

            flag_assume_valid = 0x1 << 15 if entry.flag_assume_valid else 0

            name_bytes = entry.name.encode("utf8")
            bytes_len = len(name_bytes)
            if bytes_len >= 0xFFF:
                name_length = 0xFFF
            else:
                name_length = bytes_len

            content += (flag_assume_valid | entry.flag_stage | name_length).to_bytes(
                2, "big"
            )

            content += name_bytes
            content += (0).to_bytes(1, "big")

            idx += 62 + len(name_bytes) + 1

            if idx % 8 != 0:
                pad = 8 - (idx % 8)
                content += (0).to_bytes(pad, "big")
                idx += pad

        repo.fs.file_write("index", content=content, root="git", overwrite=True)
