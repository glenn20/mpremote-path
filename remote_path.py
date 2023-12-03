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
from functools import lru_cache
from pathlib import Path, PosixPath
from typing import Generator, Iterable, Iterator

from board import Board


class RemoteDirEntry:
    """A duck-typed version of `os.DirEntry` for use with `RemotePath`.

    Will be initialised from the results of calling `os.ilistdir()` on the
    micropython board. This is used to support the `_scandir()`, `glob()` and
    `rglob()` methods of `RemotePath`."""

    def __init__(self, path: str, mode: int = 0, inode: int = 0, size: int = 0) -> None:
        self.path: str = path
        self._mode: int = mode
        self._inode: int = hash(self.path)
        self._size: int = size
        self._stat: os.stat_result | None = None

    @property
    def name(self) -> str:
        return self.path.split("/")[-1]

    def inode(self) -> int:
        return self._inode

    def is_dir(self, *, follow_symlinks: bool = True) -> bool:
        return stat.S_ISDIR(self._mode)

    def is_file(self, *, follow_symlinks: bool = True) -> bool:
        return stat.S_ISREG(self._mode)

    def is_symlink(self) -> bool:
        return stat.S_ISLNK(self._mode)

    def stat(self, *, follow_symlinks: bool = True) -> os.stat_result:
        if self._stat is None:
            if not RemotePath.board:
                raise ValueError("RemotePath.board must be set before use.")
            s = RemotePath.board.eval(f"os.stat({self.path!r})")
            self._stat = os.stat_result(s)
        return self._stat


# Paths on the board are always Posix paths even if local host is Windows.
class RemotePath(PosixPath):
    "A `pathlib.Path` compatible class to hold details of files on the board."
    slots = ("_stat", "board")
    epoch_offset: int = 0
    board: Board
    _stat: os.stat_result | None

    def __new__(cls, *args, **kwargs) -> Path:
        if not cls.board:
            raise ValueError("RemotePath.board must be set before use.")
        self = cls._from_parts(args)  # type: ignore
        self.board = kwargs.get("board", self.__class__.board)
        self._flavour.has_drv = True
        return self

    def __init__(self, *args, **kwargs) -> None:
        self._stat = None

    def __repr__(self) -> str:
        return (
            f"RemotePath({self.as_posix()!r},stat={self._stat})"
            if hasattr(self, "_stat")
            else f"RemotePath({self.as_posix()!r})"
        )

    @classmethod
    def cwd(cls) -> Path:
        if not cls.board:
            raise ValueError("RemotePath.board must be set before use.")
        return cls(cls.board.eval("os.getcwd()"))

    @classmethod
    def home(cls) -> Path:
        return cls("/")

    def cd(self) -> Path:
        p = self.resolve()
        self.board.exec(f"os.chdir({p.as_posix()!r})")
        return p

    def samefile(self, other: Path | str) -> bool:
        raise NotImplementedError

    def iterdir(self) -> Iterator[Path]:
        for name in self.board.eval(f"os.listdir({str(self)!r})"):
            yield self._make_child_relpath(name)  # type: ignore

    # `rglob()` calls `_scandir()` twice in a row for each dir, so cache the
    # results from the board.
    # !!! Fixme: replace with real caching.
    @lru_cache(maxsize=1)
    def _ilistdir(self) -> Iterable[RemoteDirEntry]:
        """Return an iterable of `RemoteDirEntry` objects for the files in a
        directory on the micropython `board`."""
        ls = self.board.eval(f"list(os.ilistdir({self.as_posix()!r}))")
        return [RemoteDirEntry(*f) for f in ls]

    # glob() and rglob() rely on _scandir()
    @contextmanager
    def _scandir(self) -> Generator[Iterable[RemoteDirEntry], None, None]:
        """A context manager which produces an iterable of information about the
        files in a folder on the micropython board. This is used by `glob()` and
        `rglob()`."""
        try:
            yield (f for f in self._ilistdir())
        finally:
            pass

    def resolve(self, strict: bool = False) -> Path:
        # The board has no concept of symlinks, so just eliminate ".." and "."
        # from the absolute path.
        parts = self._parts if self.is_absolute() else ([self.cwd()] + self._parts)  # type: ignore
        new_parts = []
        for p in parts:
            if p == ".." and new_parts:
                new_parts.pop()
            elif p != ".":
                new_parts.append(p)
        return self._from_parts(new_parts) if new_parts != parts else self  # type: ignore

    def stat(self) -> os.stat_result:
        if hasattr(self, "_stat") and self._stat is not None:
            return self._stat
        with self.board.raw_repl() as r:
            self._stat = r.fs_stat(self.as_posix())
        if self._stat is None:
            raise FileNotFoundError(f"No such file or directory: {self.as_posix()!r}")
        return self._stat

    def owner(self) -> str:
        return "root"

    def group(self) -> str:
        return "root"

    def open(self, mode="r", buffering=-1, encoding=None, errors=None, newline=None):
        raise NotImplementedError

    def read_bytes(self) -> bytes:
        with self.board.raw_repl() as r:
            return r.fs_readfile(self.as_posix())

    def read_text(self, encoding=None, errors=None) -> str:
        return self.read_bytes().decode(encoding or "utf-8", errors or "strict")

    def write_bytes(self, data: bytes) -> None:
        self._stat = None
        with self.board.raw_repl() as r:
            r.fs_writefile(self.as_posix(), data)

    def write_text(self, data, encoding=None, errors=None, newline=None):
        return self.write_bytes(data.encode(encoding or "utf-8", errors or "strict"))

    def readlink(self):
        raise NotImplementedError

    def touch(self, mode=0o666, exist_ok=True) -> None:
        self._stat = None
        with self.board.raw_repl() as r:
            r.fs_touch(self.as_posix())

    def mkdir(self, mode=0o777, parents=False, exist_ok=False) -> None:
        self._stat = None
        with self.board.raw_repl() as r:
            r.fs_mkdir(self.as_posix())

    def chmod(self, mode: int, *, follow_symlinks=True) -> None:
        raise NotImplementedError

    def lchmod(self, mode: int) -> None:
        raise NotImplementedError

    def unlink(self, missing_ok=False) -> None:
        self._stat = None
        with self.board.raw_repl() as r:
            r.fs_rm(self.as_posix())

    def rmdir(self) -> None:
        self._stat = None
        with self.board.raw_repl() as r:
            r.fs_rmdir(self.as_posix())

    def lstat(self) -> os.stat_result:
        return self.stat()

    def rename(self, target: RemotePath | str) -> Path:
        self._stat = None
        self.board.exec(f"os.rename({self.as_posix()!r},{str(target)!r})")
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
        try:
            self.stat()
        except FileNotFoundError:
            return False
        return True

    def is_dir(self) -> bool:
        return stat.S_ISDIR(self.stat().st_mode)

    def is_file(self) -> bool:
        return stat.S_ISREG(self.stat().st_mode)

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
