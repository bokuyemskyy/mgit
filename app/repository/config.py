from configparser import ConfigParser


def default_config() -> ConfigParser:
    config = ConfigParser()
    config.add_section("core")
    config.set("core", "repositoryformatversion", "0")
    config.set("core", "filemode", "false")
    config.set("core", "bare", "false")
    return config
