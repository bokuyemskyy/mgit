import os
from typing import Dict, Union

RefTree = Dict[str, Union[str, "RefTree"]]


class GitReferences:
    def __init__(self, fs):
        self.fs = fs

    def resolve(self, ref: str, max_depth: int = 64) -> str:
        depth = 0
        while True:
            if depth >= max_depth:
                raise RecursionError(
                    f"Too many symbolic ref indirections (>{max_depth})"
                )
            path = self.fs.file_require(ref)
            with open(path, "r", encoding="utf-8") as f:
                data = f.read().strip()
            if data.startswith("ref: "):
                ref = data[5:]
                depth += 1
                continue
            return data

    def list(self, path: str = "refs") -> RefTree:
        dir_path = self.fs.dir_require(path)
        result: RefTree = {}
        for entry in sorted(os.listdir(dir_path)):
            full_path = os.path.join(dir_path, entry)
            name = os.path.join(path, entry)
            if os.path.isdir(full_path):
                result[entry] = self.list(name)
            else:
                result[entry] = self.resolve(name)
        return result

    def create(self, *subpath: str, sha: str) -> str:
        return self.fs.file_ensure("refs", *subpath, content=sha + "\n")
