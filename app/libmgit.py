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

argsp = argsubparsers.add_parser("log", help="Show history of a given commit")
argsp.add_argument("commit", default="HEAD", nargs="?", help="Starting commit")

argsp = argsubparsers.add_parser("ls-tree", help="Print a tree object")
argsp.add_argument(
    "-r", dest="recursive", action="store_true", help="Recurse into sub-trees"
)


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
        case "log":
            command_log(args)
        #        case "ls-files":
        #            command_ls_files(args)
        case "ls-tree":
            command_ls_tree(args)
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
    fmt: bytes

    def __init__(self, raw=None):
        if raw is not None:
            self.deserialize(raw)
        else:
            self.init()

    @abstractmethod
    def deserialize(self, raw) -> None:
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
                constructor = GitCommit
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

    def deserialize(self, raw):
        self.blobdata = raw


def command_cat_file(args):
    repository = repository_find()
    cat_file(repository, args.object, args.type.encode())


def cat_file(repository, sha: str, fmt=None):
    object = object_read(repository, object_find(repository, sha, fmt=fmt))
    if not isinstance(object, GitObject):
        raise ValueError(f"Not an object: {sha}")
    print(object.serialize().decode("ascii"))


def object_find(repository, sha, fmt=None, follow=True):
    return sha


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

    def serialize(self, repository=None):
        return kvlm_serialize(self.kvlm)

    def deserialize(self, raw):
        self.kvlm = kvlm_deserialize(raw)

    def init(self):
        self.kvlm = dict()


class GitTag(GitCommit):
    fmt = b"tag"


class GitTree(GitObject):
    fmt = b"tree"

    def serialize(self, repository=None):
        pass
        # return tree_serialize(self)

    def deserialize(self, raw):
        pass
        # self.items = tree_parse(data)

    def init(self):
        self.items = list()


def kvlm_deserialize(raw, kvlm=None):
    size = len(raw)

    if kvlm is None:
        kvlm = dict()

    pos = 0
    while pos < size:
        space = raw.find(b" ", pos)
        newline = raw.find(b"\n", pos)

        if (space < 0) or (newline < space):
            if newline != pos:
                raise ValueError(f"Expected blank line at position {pos}")
            kvlm[None] = raw[pos + 1 :]
            return kvlm

        key = raw[pos:space]

        end = pos

        while True:
            end = raw.find(b"\n", end + 1)
            if raw[end + 1] != ord(" "):
                break

        value = raw[space + 1 : end].replace(b"\n ", b"\n")

        if key in kvlm:
            kvlm[key].append(value)
        else:
            kvlm[key] = [value]

        pos = end + 1

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


def command_log(args):
    repository = repository_find()

    seen = set()

    for sha in iterate_commits(repository, args.commit, seen):
        commit = object_read(repository, sha)
        print_commit(commit, sha)


def iterate_commits(repository, sha, seen):
    if sha in seen:
        return

    seen.add(sha)
    commit = object_read(repository, sha)

    if not isinstance(commit, GitCommit):
        raise ValueError(f"Object {sha} is not a commit")

    parents = commit.kvlm.get(b"parent", [])

    if not isinstance(parents, list):
        parents = [parents]

    for parent in parents:
        yield from iterate_commits(repository, parent, seen)

    yield sha


def print_commit(commit: GitCommit, sha):
    kvlm = commit.kvlm

    print(f"commit {sha.decode("ascii")}")
    if b"author" in kvlm:
        print(f"Author: {kvlm[b"author"].decode("utf-8")}")
    if b"date" in kvlm:
        print(f"Date:   {kvlm[b"date"].decode("utf-8")}")
    message = kvlm.get(None, b"").decode("utf-8")

    print()
    for line in message.splitlines():
        print(f"    {line}")
    print()


class GitTreeLeaf(object):
    def __init__(self, mode, path, sha):
        self.mode = mode
        self.path = path
        self.sha = sha


def tree_deserialize(raw):
    pos = 0
    size = len(raw)
    result = list()

    while pos < size:
        pos, node_raw = tree_node_deserialize(raw, pos)
        result.append(raw)

    return result


def tree_node_deserialize(raw, pos=0):
    mode_separator = raw.find(b" ", pos)
    if mode_separator - pos != 5 and mode_separator - pos != 6:
        raise ValueError("Missing mode separator")

    mode = raw[pos:mode_separator]
    if len(mode) == 5:
        mode = b"0" + mode

    path_separator = raw.find(b"\x00", mode_separator)
    if path_separator < 0:
        raise ValueError("Missing path separator")
    path = raw[mode_separator + 1 : path_separator]

    raw_sha = int.from_bytes(raw[path_separator + 1 : path_separator + 21], "big")
    sha = format(raw_sha, "040x")

    return path_separator + 21, GitTreeLeaf(mode, path.decode("utf8"), sha)


def tree_leaf_sort_key(leaf):
    if leaf.mode.startswith(b"10"):
        return leaf.path
    else:
        return leaf.path + "/"


def tree_serialize(object):
    result = b""

    object.items.sort(key=tree_leaf_sort_key)
    for item in object.items:
        result += item.mode
        result += b" "
        result += item.path.encode()
        result += b"\x00"
        sha = int(item.sha, 16)
        result += sha.to_bytes(20, "big")

    return result


class GitTree(GitObject):
    fmt = b"tree"

    def deserialize(self, raw) -> None:
        self.items = tree_deserialize(raw)

    def serialize(self, repository=None) -> bytes:
        return tree_serialize(self)

    def init(self):
        self.items = list()


def command_ls_tree(args):
    repository = repository_find()
    ls_tree(repository, args.tree, args.recursive)


def ls_tree(repository, sha, recursive=None, prefix=""):
    name = object_find(repository, sha, fmt=b"tree")
    object = object_read(repository, name)

    if not isinstance(object, GitTree):
        raise ValueError(f"Object is not a tree: {sha}")

    for item in object.items:
        if len(item.mode) == 5:
            type = item.mode[0:1]
        else:
            type = item.mode[0:2]

        match type:
            case b"04":
                type = "tree"
            case b"10":
                type = "blob"
            case b"12":
                type = "blob"
            case b"16":
                type = "commit"
            case _:
                raise Exception(f"Unknown object type: {item.mode}")

        if not (recursive and type == "tree"):
            print(
                f"{"0" * (6 - len(item.mode)) + item.mode.decode("ascii")} {type} {item.sha}\t{os.path.join(prefix, item.path)}"
            )
        else:
            ls_tree(repository, item.sha, recursive, os.path.join(prefix, item.path))


def command_checkout(args):
    repository = repository_find()

    sha = object_find(repository, args.commit)
    object = object_read(repository, sha)

    if not isinstance(object, GitCommit):
        raise ValueError(f"Object is not a commit: {sha}")

    object = object_read(repository, object.kvlm[b"tree"].decode("ascii"))

    if os.path.exists(args.path):
        if not os.path.isdir(args.path):
            raise Exception(f"Not a directory {args.path}")
        if os.listdir(args.path):
            raise Exception(f"Not empty {args.path}")
    else:
        os.makedirs(args.path)

    tree_checkout(repository, object, os.path.realpath(args.path))


def tree_checkout(repository, tree, path):
    for item in tree.items:
        object = object_read(repository, item.sha)
        destination = os.path.join(path, item.path)

        assert object is not None

        if object.fmt == b"tree":
            os.mkdir(destination)
            tree_checkout(repository, object, destination)
        elif object.fmt == b"blob":
            with open(destination, "wb") as file:
                assert isinstance(object, GitBlob)
                file.write(object.blobdata)
