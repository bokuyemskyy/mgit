from __future__ import annotations

from abc import ABC, abstractmethod

class GitObject(ABC):
    fmt: bytes

    def __init__(self):
        self.initialize()

    @abstractmethod
    def initialize(self) -> None:
        pass

    @abstractmethod
    def serialize(self) -> bytes:
        pass

    @classmethod
    @abstractmethod
    def deserialize(cls, data: bytes) -> GitObject:
        pass
