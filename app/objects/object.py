from __future__ import annotations

from typing import Optional, TypeVar, Type
from abc import ABC, abstractmethod
from app.repository import GitRepository


class GitObject(ABC):
    fmt: bytes

    def __init__(self):
        self.initialize()

    @abstractmethod
    def initialize(self) -> None:
        pass

    @abstractmethod
    def serialize(self, repository: Optional[GitRepository] = None) -> bytes:
        pass

    @classmethod
    @abstractmethod
    def deserialize(cls, data: bytes) -> GitObject:
        pass
