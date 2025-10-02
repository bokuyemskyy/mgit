import os
from typing import Union


class GitFilesystem:
    def __init__(self, worktree: str, gitdir: str):
        self.worktree = worktree
        self.gitdir = gitdir

    def resolve_path(self, *subpath: str) -> str:
        return os.path.join(self.gitdir, *subpath)

    def dir_exists(self, *subpath: str) -> bool:
        return os.path.isdir(self.resolve_path(*subpath))

    def dir_ensure(self, *subpath: str) -> str:
        path = self.resolve_path(*subpath)
        os.makedirs(path, exist_ok=True)
        if not os.path.isdir(path):
            raise NotADirectoryError(f"Failed to create directory: {path}")
        return path

    def dir_require(self, *subpath: str) -> str:
        path = self.resolve_path(*subpath)
        if not os.path.isdir(path):
            raise NotADirectoryError(f"Required dir not found: {path}")
        return path

    def file_exists(self, *subpath: str) -> bool:
        return os.path.isfile(self.resolve_path(*subpath))

    def file_ensure(
        self,
        *subpath: str,
        content: Union[str, bytes, None] = None,
        overwrite: bool = False,
    ) -> str:
        self.dir_ensure(*subpath[:-1])
        path = self.resolve_path(*subpath)
        if os.path.exists(path):
            if not os.path.isfile(path):
                raise IsADirectoryError(f"Is a directory: {path}")
            if not overwrite:
                return path
        if content is not None:
            if isinstance(content, bytes):
                with open(path, "wb") as f:
                    f.write(content)
            elif isinstance(content, str):
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
        else:
            open(path, "wb").close()
        return path

    def file_require(self, *subpath: str) -> str:
        path = self.resolve_path(*subpath)
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Required file not found: {path}")
        return path
