from app.repository.repository import GitRepository
from .object import GitObject


class GitTree(GitObject):
    format = b"tree"
    items: list

    def initialize(self):
        self.items = list()

    def serialize(self, repository: GitRepository | None = None) -> bytes:
        return tree_serialize(self)

    def deserialize(self, raw: bytes) -> None:
        self.items = tree_deserialize(raw)


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
