import argparse


# from datetime import datetime
# import grp, pwd

from typing import Optional

# from fnmatch import fnmatch

import hashlib

# from math import ceil


# import re
import sys

import zlib


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

        if isinstance(object, GitTree):
            os.mkdir(destination)
            tree_checkout(repository, object, destination)
        elif isinstance(object, GitBlob):
            with open(destination, "wb") as file:
                assert isinstance(object, GitBlob)
                file.write(object.blobdata)
