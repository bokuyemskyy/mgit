from configparser import ConfigParser
import os


def default_config() -> ConfigParser:
    config = ConfigParser()
    config.add_section("core")
    config.set("core", "repositoryformatversion", "0")
    config.set("core", "filemode", "false")
    config.set("core", "bare", "false")
    return config


def read_all_configs(gitdir: str):
    gitdir = os.path.realpath(gitdir)

    xdg_config_home = (
        os.environ["XDG_CONFIG_HOME"]
        if "XDG_CONFIG_HOME" in os.environ
        else "~/.config"
    )
    config_files = [
        "/etc/gitconfig",
        os.path.expanduser(os.path.join(xdg_config_home, "git/config")),
        os.path.expanduser("~/.gitconfig"),
        os.path.expanduser(os.path.join(gitdir, "config")),
    ]
    config_files = [f for f in config_files if os.path.exists(f)]

    config = default_config()
    config.read(config_files)
    return config
