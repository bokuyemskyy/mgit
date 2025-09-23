from app.repository.repository import GitRepository
from .object import GitObject


class GitBlob(GitObject):
    format = b"blob"
    blobdata: bytes

    def initialize(self):
        self.blobdata = b""

    def serialize(self, repository: GitRepository | None = None) -> bytes:
        return self.blobdata

    def deserialize(self, raw: bytes) -> None:
        self.blobdata = raw
