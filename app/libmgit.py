import argparse
import configparser

from abc import ABC, abstractmethod

# from datetime import datetime
# import grp, pwd

from typing import Optional

# from fnmatch import fnmatch

import hashlib

# from math import ceil

import os

# import re
import sys

import zlib

argparser = argparse.ArgumentParser()
argsubparsers = argparser.add_subparsers(title="Commands", dest="command")
argsubparsers.required = True
argsp = argsubparsers.add_parser("init", help="Initialize an empty repository")
argsp.add_argument(
    "path",
    metavar="directory",
    nargs="?",
    default=".",
    help="Where to create the repository",
)
argsp = argsubparsers.add_parser(
    "cat-file", help="Cat the content of repository object"
)

argsp.add_argument(
    "type",
    metavar="type",
    choices=["blob", "commit", "tag", "tree"],
    help="Specify the type",
)

argsp.add_argument("object", metavar="object", help="Object to display")
argsp = argsubparsers.add_parser(
    "hash-object",
    help="Compute the object's hash and optionally create a blob from the file",
)
argsp.add_argument(
    "-t",
    metavar="type",
    dest="type",
    choices=["blob", "commit", "tag", "tree"],
    default="blob",
    help="Specify the type",
)

argsp.add_argument(
    "-w",
    dest="write",
    action="store_true",
    help="Write the object into the database",
)

argsp.add_argument("path", help="Source for the object")


def main(argv=sys.argv[1:]):
    args = argparser.parse_args(argv)
    match args.command:
        #        case "add":
        #            command_add(args)
        case "cat-file":
            command_cat_file(args)
        #        case "check-ignore":
        #            command_check_ignore(args)
        #        case "checkout":
        #            command_checkout(args)
        #        case "commit":
        #            command_commit(args)
        case "hash-object":
            command_hash_object(args)
        case "init":
            command_init(args)
        #    '''    case "log":
        #            commandf_log(args)
        #        case "ls-files":
        #            command_ls_files(args)
        #        case "ls-tree":
        #            command_ls_tree(args)
        #        case "rev-parse":
        #            command_rev_parse(args)
        #        case "rm":
        #            command_rm(args)
        #        case "show-ref":
        #            command_show_ref(args)
        #        case "status":
        #            command_status(args)
        #        case "tag":
        #            command_tag(args)
        case _:
            print(f"Invalid command: {args.command}")


class GitRepository(object):
    worktree: str
    gitdir: str
    config: configparser.ConfigParser = configparser.ConfigParser()

    def __init__(self, path, force=False) -> None:
        self.worktree = path
        self.gitdir = os.path.join(path, ".git")

        if not os.path.isdir(self.gitdir) and not force:
            raise Exception(f"Not a git repository: {path}")

        config_file = repository_file(self, "config")

        if config_file and os.path.exists(config_file):
            self.config.read([config_file])
        elif not force:
            raise Exception("Configuration file not found")

        if not force:
            version = int(self.config.get("core", "repositoryformatversion"))
            if version != 0:
                raise Exception(f"Unsupported repositoryformatversion: {version}")


def repository_path(repository, *path: str) -> str:
    assert repository.gitdir is not None
    return os.path.join(repository.gitdir, *path)


def repository_file(repository, *path: str, mkdir=False) -> Optional[str]:
    if repository_dir(repository, *path[:-1], mkdir=mkdir):
        return repository_path(repository, *path)


def repository_dir(repository, *path, mkdir=False) -> Optional[str]:
    path = repository_path(repository, *path)

    if os.path.exists(path):
        if os.path.isdir(path):
            return path
        else:
            raise Exception(f"Not a directory: {path}")

    if mkdir:
        os.makedirs(path)
        return path
    else:
        return None


def repository_create(path) -> GitRepository:
    repository = GitRepository(path, True)

    if os.path.exists(repository.worktree):
        if not os.path.isdir(repository.worktree):
            raise Exception(f"{path} is not a directory")
        if os.path.exists(repository.gitdir) and os.listdir(repository.gitdir):
            raise Exception(f"{path} is not empty")
    else:
        os.makedirs(repository.worktree)

    if repository_dir(repository, "branches", mkdir=True) is None:
        raise RuntimeError("branches directory was not created")
    if repository_dir(repository, "objects", mkdir=True) is None:
        raise RuntimeError("objects directory was not created")
    if repository_dir(repository, "refs", "tags", mkdir=True) is None:
        raise RuntimeError("tags directory was not created")
    if repository_dir(repository, "refs", "heads", mkdir=True) is None:
        raise RuntimeError("heads directory was not created")

    description_file = repository_file(repository, "description")
    if description_file is None:
        raise RuntimeError("description file was not created")
    with open(description_file, "w") as description:
        description.write("Unnamed repository")

    head_file = repository_file(repository, "HEAD")
    if head_file is None:
        raise RuntimeError("HEAD file was not created")
    with open(head_file, "w") as head:
        head.write("ref: refs/heads/master\n")

    config_file = repository_file(repository, "config")
    if config_file is None:
        raise RuntimeError("config file was not created")
    with open(config_file, "w") as config:
        default_config = repository_default_config()
        default_config.write(config)

    return repository


def repository_default_config():
    config = configparser.ConfigParser()

    config.add_section("core")
    config.set("core", "repositoryformatversion", "0")
    config.set("core", "filemode", "false")
    config.set("core", "bare", "false")

    return config


def command_init(args):
    repository_create(args.path)


def repository_find(path=".", required=True):
    path = os.path.realpath(path)

    if os.path.isdir(os.path.join(path, ".git")):
        return GitRepository(path)

    parent = os.path.realpath(os.path.join(path, ".."))

    if parent == path:
        if required:
            raise Exception("No git repository found")
        else:
            return None

    return repository_find(parent, required)


class GitObject(ABC):
    def __init__(self, data=None):
        if data is not None:
            self.deserialize(data)
        else:
            self.init()

    @abstractmethod
    def deserialize(self, data) -> None:
        pass

    @abstractmethod
    def serialize(self, repository=None) -> bytes:
        pass

    def init(self):
        pass


def object_read(repository, sha) -> Optional[GitObject]:
    path = repository_file(repository, "objects", sha[:2], sha[2:])

    assert path is not None
    if not os.path.isfile(path):
        return None

    with open(path, "rb") as object:
        raw = zlib.decompress(object.read())

        fmt_separator = raw.find(b" ")
        if fmt_separator < 0:
            raise ValueError("Missing type separator")
        object_fmt = raw[:fmt_separator]

        size_separator = raw.find(b"\x00", fmt_separator)
        if size_separator < 0:
            raise ValueError("Missing size separator")

        object_size = int(raw[fmt_separator:size_separator].decode("ascii"))
        if object_size != len(raw) - size_separator - 1:
            raise Exception(f"Malformed object {sha}: bad length")

        match object_fmt:
            case b"commit":
                constructor = GitBlob  # GitCommit
            case b"tree":
                constructor = GitBlob  # GitTree
            case b"tag":
                constructor = GitBlob  # GitTag
            case b"blob":
                constructor = GitBlob
            case _:
                raise Exception(
                    f"Unknown object type {object_fmt.decode("ascii")} for object{sha}"
                )

        return constructor(raw[size_separator + 1 :])


def object_write(object, repository=None):
    data = object.serialize()

    raw = object.fmt + b" " + str(len(data)).encode() + b"\x00" + data

    sha = hashlib.sha1(raw).hexdigest()

    if repository:
        path = repository_file(repository, "objects", sha[:2], sha[2:], mkdir=True)

        if path is None:
            raise RuntimeError("Object directory was not created")
        if not os.path.exists(path):
            with open(path, "wb") as object_file:
                object_file.write(zlib.compress(raw))

    return sha


class GitBlob(GitObject):
    fmt = b"blob"

    def serialize(self, repository=None):
        return self.blobdata

    def deserialize(self, data):
        self.blobdata = data


def command_cat_file(args):
    repository = repository_find()
    cat_file(repository, args.object, args.type.encode())


def cat_file(repository, name: str, fmt=None):
    object = object_read(repository, object_find(repository, name, fmt=fmt))
    assert isinstance(object, GitObject)
    print(object.serialize().decode("ascii"))


def object_find(repository, name, fmt=None, follow=True):
    return name


def command_hash_object(args):
    repository = None

    if args.write:
        repository = repository_find()

    with open(args.path, "rb") as object_file:
        sha = object_hash(object_file, args.type.encode(), repository)
        print(sha)


def object_hash(file, fmt, repository=None):
    raw = file.read()

    match fmt:
        case b"commit":
            object = GitCommit(raw)
        case b"tree":
            object = GitTree(raw)
        case b"tag":
            object = GitTag(raw)
        case b"blob":
            object = GitBlob(raw)
        case _:
            raise Exception(f"Unknown object type {fmt.decode("ascii")}")

    return object_write(object, repository)


class GitCommit(GitObject):
    fmt = b"commit"

    def deserialize(self, data):
        pass

    #    self.kvlm = kvlm_parse(data)

    def serialize(self, repository=None) -> bytes:
        pass

    #    return kvlm_serialize(self.kvlm)

    def init(self):
        self.kvlm = dict()


class GitTag(GitCommit):
    fmt = b"tag"


class GitTree(GitObject):
    fmt = b"tree"

    def deserialize(self, data):
        pass
        # self.items = tree_parse(data)

    def serialize(self, repository=None):
        pass
        # return tree_serialize(self)

    def init(self):
        self.items = list()


def kvlm_deserialize(raw, kvlm=None):
    size = len(raw)

    if kvlm is None:
        kvlm = dict()

    start = 0
    while start < size:
        space = raw.find(b" ", start)
        newline = raw.find(b"\n", start)

        if (space < 0) or (newline < space):
            if newline != start:
                raise ValueError(f"Expected blank line at position {start}")
            kvlm[None] = raw[start + 1 :]
            return kvlm

        key = raw[start:space]

        end = start

        while True:
            end = raw.find(b"\n", end + 1)
            if raw[end + 1] != ord(" "):
                break

        value = raw[space + 1 : end].replace(b"\n ", b"\n")

        if key in kvlm:
            kvlm[key].append(value)
        else:
            kvlm[key] = [value]

        start = end + 1

    return kvlm


def kvlm_serialize(kvlm):
    result = b""

    for key in kvlm.keys():
        if key == None:
            continue

        values = kvlm[key]

        for value in values:
            result += key + b" " + value.replace(b"\n", b"\n ") + b"\n"

    result += b"\n" + kvlm[None]

    return result
