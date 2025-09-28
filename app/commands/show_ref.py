from __future__ import annotations
import os
from typing import Union, Dict
from argparse import _SubParsersAction

from app.repository import (
    repository_find,
    repository_file,
    repository_dir,
    GitRepository
)

RefTree = Dict[str, Union[str, "RefTree"]]


def setup_parser(subparsers: _SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "show-ref",
        help="Show references"
    )
    parser.set_defaults(func=command_show_ref)


def command_show_ref(args) -> None:
    repo = repository_find()
    refs = ref_list(repo)
    show_ref(refs, prefix="refs")


def show_ref(refs: RefTree, with_hash: bool = True, prefix: str = "") -> None:
    for name, value in refs.items():
        ref_path = f"{prefix}/{name}" if prefix else name

        if isinstance(value, str):
            print(f"{value} {ref_path}" if with_hash else ref_path)
        elif isinstance(value, dict):
            show_ref(value, with_hash=with_hash, prefix=ref_path)
        else:
            raise TypeError("Unexpected ref value type")


def ref_resolve(repo: GitRepository, ref: str) -> str:
    while True:
        path = repository_file(repo, ref)
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Ref not found: {path}")

        with open(path, "r") as ref_file:
            data = ref_file.read().strip()

        if data.startswith("ref: "):
            ref = data[5:]
            continue
        return data


def ref_list(repo: GitRepository, path: str = "refs") -> RefTree:
    refs_dir = repository_dir(repo, path)
    result: RefTree = {}

    for entry in sorted(os.listdir(refs_dir)):
        full_path = os.path.join(refs_dir, entry)
        ref_name = os.path.join(path, entry)

        if os.path.isdir(full_path):
            result[entry] = ref_list(repo, ref_name)
        else:
            result[entry] = ref_resolve(repo, ref_name)

    return result
