import os
import configparser

from typing import Optional

from .repository import GitRepository, repository_file


def repository_default_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config.add_section("core")
    config.set("core", "repositoryformatversion", "0")
    config.set("core", "filemode", "false")
    config.set("core", "bare", "false")
    return config


def read_config(repository: GitRepository) -> configparser.ConfigParser:
    config_file = repository_file(repository, "config")
    config = configparser.ConfigParser()
    if config_file and os.path.exists(config_file):
        config.read([config_file])
    return config


def write_config(
    repository: GitRepository, config: Optional[configparser.ConfigParser] = None
) -> None:
    if not config:
        config = repository_default_config()
    repository.config = config
    config_path = repository_file(repository, "config", mkdir=True)
    with open(config_path, "w") as config_file:
        config.write(config_file)
