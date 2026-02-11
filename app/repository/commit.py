import os
from typing import Dict, Union

from app.objects import GitTree, GitTreeLeaf

from .index import GitIndex, GitIndexEntry
from .repository import GitRepository


def tree_to_dict(repo: GitRepository, ref: str, prefix=""):
    result = {}

    sha = repo.objects.find(ref, fmt=b"tree")
    tree = repo.objects.read(sha)

    assert isinstance(tree, GitTree)

    for leaf in tree.items:
        full_path = os.path.join(prefix, leaf.path)

        is_subtree = leaf.mode.startswith(b"04")

        if is_subtree:
            result.update(tree_to_dict(repo, leaf.sha, full_path))
        else:
            result[full_path] = leaf.sha
    return result


TreeDict = Dict[str, Union["TreeDict", GitIndexEntry]]


def tree_from_index(repo: GitRepository, index: GitIndex) -> str:
    root: TreeDict = {}

    for entry in index.entries:
        parts = entry.name.split("/")
        current = root

        for part in parts[:-1]:
            if part not in current:
                current[part] = {}

            node = current[part]

            if isinstance(node, dict):
                current = node

            else:
                raise TypeError(f"Path conflict at {part}")

        current[parts[-1]] = entry

    def write_tree_recursive(node_dict: dict) -> str:
        tree = GitTree()
        for name, value in sorted(node_dict.items()):
            if isinstance(value, GitIndexEntry):
                # It is a file
                mode = f"{value.mode_type:o}{value.mode_perms:04o}".encode("ascii")
                tree.items.append(GitTreeLeaf(mode, name, value.sha))
            else:
                # It is a directory
                subtree_sha = write_tree_recursive(value)
                tree.items.append(GitTreeLeaf(b"40000", name, subtree_sha))

        return repo.objects.write(tree)

    return write_tree_recursive(root)
