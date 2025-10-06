import os
import shutil
from typing import Union, Literal, Optional, overload


class GitFilesystem:
    def __init__(self, worktree: str, gitdir: str):
        self.worktree = os.path.realpath(worktree)
        self.gitdir = os.path.realpath(gitdir)

    def resolve(self, *subpath: str, root: Literal["git", "worktree"] = "git") -> str:
        base = self.gitdir if root == "git" else self.worktree
        return os.path.join(base, *subpath)

    def dir_exists(
        self, *subpath: str, root: Literal["git", "worktree"] = "git"
    ) -> bool:
        return os.path.isdir(self.resolve(*subpath, root=root))

    def dir_ensure(
        self, *subpath: str, root: Literal["git", "worktree"] = "git"
    ) -> str:
        path = self.resolve(*subpath, root=root)
        os.makedirs(path, exist_ok=True)
        if not os.path.isdir(path):
            raise NotADirectoryError(f"Failed to create directory: {path}")
        return path

    def dir_require(
        self, *subpath: str, root: Literal["git", "worktree"] = "git"
    ) -> str:
        path = self.resolve(*subpath, root=root)
        if not os.path.isdir(path):
            raise NotADirectoryError(f"Required dir not found: {path}")
        return path

    def dir_delete(
        self,
        *subpath: str,
        root: Literal["git", "worktree"] = "git",
        recursive: bool = False,
    ) -> None:
        path = self.resolve(*subpath, root=root)
        if not os.path.exists(path):
            return

        if os.path.isdir(path):
            if recursive:
                shutil.rmtree(path)
            else:
                os.rmdir(path)
        else:
            raise NotADirectoryError(f"Cannot delete directory: {path} is a file")

    def file_exists(
        self, *subpath: str, root: Literal["git", "worktree"] = "git"
    ) -> bool:
        return os.path.isfile(self.resolve(*subpath, root=root))

    def file_require(
        self, *subpath: str, root: Literal["git", "worktree"] = "git"
    ) -> str:
        path = self.resolve(*subpath, root=root)
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Required file not found: {path}")
        return path

    @overload
    def file_read(
        self,
        *subpath: str,
        root: Literal["git", "worktree"] = "git",
        binary: Literal[False],
    ) -> str: ...

    @overload
    def file_read(
        self,
        *subpath: str,
        root: Literal["git", "worktree"] = "git",
        binary: Literal[True],
    ) -> bytes: ...

    def file_read(
        self,
        *subpath: str,
        root: Literal["git", "worktree"] = "git",
        binary: bool = True,
    ) -> Union[bytes, str]:
        path = self.file_require(*subpath, root=root)
        mode = "rb" if binary else "r"
        encoding = None if binary else "utf-8"

        with open(path, mode, encoding=encoding) as f:
            return f.read()

    def file_write(
        self,
        *subpath: str,
        content: Union[str, bytes],
        root: Literal["git", "worktree"] = "git",
        overwrite: bool = True,
    ) -> str:
        self.dir_ensure(*subpath[:-1], root=root)
        path = self.resolve(*subpath, root=root)

        if os.path.exists(path) and not overwrite:
            return path

        mode = "wb" if isinstance(content, bytes) else "w"
        encoding = "utf-8" if isinstance(content, str) else None

        with open(path, mode, encoding=encoding) as f:
            f.write(content)

        return path

    def file_ensure(
        self,
        *subpath: str,
        content: Union[str, bytes, None] = None,
        overwrite: bool = False,
        root: Literal["git", "worktree"] = "git",
    ) -> str:
        if content is not None:
            return self.file_write(
                *subpath, content=content, root=root, overwrite=overwrite
            )

        path = self.resolve(*subpath, root=root)
        if os.path.exists(path):
            if not os.path.isfile(path):
                raise IsADirectoryError(f"Is a directory: {path}")
            return path

        open(path, "wb").close()
        return path

    def file_delete(
        self,
        *subpath: str,
        root: Literal["git", "worktree"] = "git",
    ) -> None:
        path = self.resolve(*subpath, root=root)
        if os.path.exists(path):
            if os.path.isfile(path):
                os.remove(path)
            else:
                raise IsADirectoryError(f"Cannot delete file: {path} is a directory.")
