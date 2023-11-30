"""Provides the "RemotePath" class which is a wrapper around the
PyBoardExtended interface to a micropython board (from the mpremote tool).
"""
# Copyright (c) 2021 @glenn20
# MIT License

# For python<3.10: Allow method type annotations to reference enclosing class
from __future__ import annotations

import os
import stat
from contextlib import contextmanager
from pathlib import Path, PurePosixPath

from board import Board


class RemoteDirEntry:
    def __init__(self, path: str, mode: int) -> None:
        self.path: str = path
        self.mode: int = mode
        self._stat: os.stat_result | None = None

    @property
    def name(self) -> str:
        return self.path.split("/")[-1]

    def inode(self) -> int:
        return hash(self.path)

    def is_dir(self, *, follow_symlinks: bool = True) -> bool:
        return (self.mode & stat.S_IFDIR) != 0

    def is_file(self, *, follow_symlinks: bool = True) -> bool:
        return (self.mode & stat.S_IFREG) != 0

    def is_symlink(self) -> bool:
        return (self.mode & stat.S_IFLNK) != 0

    def stat(self, *, follow_symlinks: bool = True) -> os.stat_result:
        if self._stat is None:
            s = RemotePath.board.eval_json(f"print(list(os.stat({self.path!r})))")
            self._stat = os.stat_result(s)
        return self._stat


@contextmanager
def RemoteScandir(path: str):
    ls = RemotePath.board.eval_json(f"print([list(i) for i in os.ilistdir({path!r})])")
    try:
        yield (RemoteDirEntry("/".join((path, f)), mode) for f, mode, *_ in ls)
    finally:
        pass


# Paths on the board are always Posix paths even if local host is Windows.
class RemotePath(Path, PurePosixPath):
    "A Pathlib compatible class to hold details of files on the board."
    __slots__ = "_stat"
    epoch_offset: int = 0
    board: Board

    def __new__(cls, *args, **kwargs):
        if not cls.board:
            raise ValueError("RemotePath.board must be set before use.")
        self = cls._from_parts(args)  # type: ignore
        return self

    def __init__(self, *_args: str) -> None:
        # Note: Path initialises from *args in __new__()!!!
        self._stat: os.stat_result | None = None

    def __repr__(self) -> str:
        return (
            f"RemotePath({self.as_posix()!r},stat={self._stat})"
            if hasattr(self, "_stat")
            else f"RemotePath({self.as_posix()!r})"
        )

    @classmethod
    def cwd(cls):
        return cls(cls.board.getcwd())

    @classmethod
    def home(cls):
        return cls("/")

    def samefile(self, other: Path | str) -> bool:
        raise NotImplementedError

    def iterdir(self):
        for name in self.board.eval_json(f"print(list(os.listdir({str(self)!r})))"):
            yield self._make_child_relpath(name)  # type: ignore

    def _scandir(self):
        return RemoteScandir(self.as_posix())

    def resolve(self, strict: bool = False) -> Path:
        return self.absolute()  # ??? need to normalise as well

    def stat(self) -> os.stat_result:
        if not hasattr(self, "_stat") or self._stat is None:
            s = self.board.eval_json(f"print(list(os.stat({str(self)!r})))")
            self._stat = os.stat_result(s)
        return self._stat

    def owner(self) -> str:
        return "root"

    def group(self) -> str:
        return "root"

    def open(self, mode="r", buffering=-1, encoding=None, errors=None, newline=None):
        raise NotImplementedError

    def read_bytes(self) -> bytes:
        with self.board.raw_repl():
            return self.board.fs_readfile(self.as_posix())

    def read_text(self, encoding=None, errors=None) -> str:
        return self.read_bytes().decode(encoding or "utf-8", errors or "strict")

    def write_bytes(self, data: bytes) -> None:
        with self.board.raw_repl():
            self.board.fs_writefile(self.as_posix(), data)

    def write_text(self, data, encoding=None, errors=None, newline=None):
        return self.write_bytes(data.encode(encoding or "utf-8", errors or "strict"))

    def readlink(self):
        raise NotImplementedError

    def touch(self, mode=0o666, exist_ok=True) -> None:
        with self.board.raw_repl():
            self.board.fs_touch(self.as_posix())

    def mkdir(self, mode=0o777, parents=False, exist_ok=False) -> None:
        with self.board.raw_repl():
            self.board.fs_mkdir(self.as_posix())

    def chmod(self, mode: int, *, follow_symlinks=True) -> None:
        raise NotImplementedError

    def lchmod(self, mode: int) -> None:
        raise NotImplementedError

    def unlink(self, missing_ok=False) -> None:
        with self.board.raw_repl():
            self.board.fs_rm(self.as_posix())

    def rmdir(self) -> None:
        with self.board.raw_repl():
            self.board.fs_rmdir(self.as_posix())

    def lstat(self) -> os.stat_result:
        return self.stat()

    def rename(self, target: RemotePath | str) -> RemotePath:
        self.board.exec2(f"os.rename({self.as_posix()!r},{str(target)!r})")
        return self.__class__(str(target))

    def replace(self, target: RemotePath | str) -> RemotePath:
        raise NotImplementedError

    def symlink_to(
        self, target: RemotePath | str, target_is_directory: bool = False
    ) -> None:
        raise NotImplementedError

    def hardlink_to(self, target: RemotePath | str) -> None:
        raise NotImplementedError

    def link_to(self, target: RemotePath | str) -> None:
        raise NotImplementedError

    def exists(self) -> bool:
        return self.stat().st_mode != 0

    def is_dir(self) -> bool:
        return (self.stat().st_mode & stat.S_IFDIR) != 0

    def is_file(self) -> bool:
        return (self.stat().st_mode & stat.S_IFREG) != 0

    def is_mount(self) -> bool:
        return False

    def is_symlink(self) -> bool:
        return False

    def is_block_device(self) -> bool:
        return False

    def is_char_device(self) -> bool:
        return False

    def is_fifo(self) -> bool:
        return False

    def is_socket(self) -> bool:
        return False

    def expanduser(self) -> RemotePath:
        return self
