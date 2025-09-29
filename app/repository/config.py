import os
import configparser
from typing import Optional


class Config:
    def __init__(self, path: str) -> None:
        self.path = path

    @staticmethod
    def default_config() -> configparser.ConfigParser:
        config = configparser.ConfigParser()
        config.add_section("core")
        config.set("core", "repositoryformatversion", str(0))
        config.set("core", "filemode", str(False).lower())
        config.set("core", "bare", str(False).lower())
        return config

    def read(self) -> configparser.ConfigParser:
        if not os.path.isfile(self.path):
            raise FileNotFoundError(f"Config file not found: {self.path}")

        config = configparser.ConfigParser()
        with open(self.path, "r", encoding="utf-8") as file:
            config.read_file(file)

        return config

    def write(self, config: Optional[configparser.ConfigParser] = None) -> None:
        if os.path.isfile(self.path):
            existing_config = configparser.ConfigParser()
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    existing_config.read_file(f)
            except Exception:
                raise RuntimeError(f"File {self.path} exists and is not a valid config")

        if config is None:
            config = self.default_config()

        with open(self.path, "w", encoding="utf-8") as file:
            config.write(file)
