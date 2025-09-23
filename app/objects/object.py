from typing import Optional
from abc import ABC, abstractmethod

from app.repository import GitRepository


class GitObject(ABC):
    format: bytes

    def __init__(self, raw: Optional[bytes] = None):
        if raw is not None:
            self.deserialize(raw)
        else:
            self.initialize()

    @abstractmethod
    def initialize(self):
        pass

    @abstractmethod
    def deserialize(self, raw: bytes) -> None:
        pass

    @abstractmethod
    def serialize(self, repository: Optional[GitRepository] = None) -> bytes:
        pass
