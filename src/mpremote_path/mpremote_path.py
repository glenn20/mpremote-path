"""Provides the `MPRemotePath` class which provides a `pathlib.Path` compatible
interface to accessing and manipulating files on micropython boards via the
`mpremote` tool.
"""

# Copyright (c) 2021 @glenn20
# MIT License

# For python<3.10: Allow method type annotations to reference enclosing class
from __future__ import annotations

import os
import stat
from contextlib import contextmanager
from pathlib import Path, PosixPath
from shutil import SameFileError
from typing import Generator, Iterable

from mpremote.transport_serial import SerialTransport

from .board import Board, make_board

START_CODE = """
def _ils(p):
  for f in os.ilistdir(p):print(f, end=',')
"""


def mpremotepath(f: str | Path) -> MPRemotePath:
    return f if isinstance(f, MPRemotePath) else MPRemotePath(f)


class MPRemoteDirEntry:
    """A duck-typed version of `os.DirEntry` for use with `MPRemotePath`.

    Will be initialised from the results of calling `os.ilistdir()` on the
    micropython board. This is used to support the `iterdir()`, `_scandir()`,
    `glob()` and `rglob()` methods of `pathlib.Path` for `MPRemotePath`s."""

    def __init__(
        self,
        parent: str,
        name: str,
        mode: int = 0,
        inode: int = 0,
        size: int = 0,
        mtime: int = 0,
    ) -> None:
        self.name: str = name
        self.parent: str = parent
        self._stat: os.stat_result = os.stat_result(
            (mode, inode, 0, 0, 0, 0, size, mtime, mtime, mtime)
        )

    @property
    def path(self) -> str:
        return f"{self.parent}/{self.name}"

    def inode(self) -> int:
        return self._stat.st_ino

    def is_dir(self, *, follow_symlinks: bool = True) -> bool:
        return stat.S_ISDIR(self._stat.st_mode)

    def is_file(self, *, follow_symlinks: bool = True) -> bool:
        return stat.S_ISREG(self._stat.st_mode)

    def is_symlink(self) -> bool:
        return stat.S_ISLNK(self._stat.st_mode)

    def stat(self, *, follow_symlinks: bool = True) -> os.stat_result:
        if self._stat is None:  # or self._stat.st_mtime == 0:
            if not MPRemotePath.board:
                raise ValueError("MPRemotePath.connect() must be called before use.")
            if self._stat is None:  # Get the full os.stat() result
                self._stat = MPRemotePath.board.fs_stat(self.path)
            else:  # We already have everything except the mtime so just fetch that
                mtime = MPRemotePath.board.eval(f"os.stat({self.path!r})[8]")
                self._stat = os.stat_result(self._stat[:7] + (mtime, mtime, mtime))
        return self._stat


# Paths on the board are always Posix paths even if local host is Windows.
class MPRemotePath(PosixPath):
    "A `pathlib.Path` compatible class to hold details of files on the board."
    slots = ("_stat", "board")
    board: Board
    _stat: os.stat_result | None
    _drv: str  # Declare types for properties inherited from pathlib classes
    _root: str
    _parts: list[str]

    def __new__(cls, *args) -> MPRemotePath:
        if not cls.board:
            raise ValueError("Must call MPRemotePath.connect() before use.")
        self = cls._from_parts(args)  # type: ignore
        self.board = self.__class__.board
        return self

    def __init__(self, *args) -> None:
        self._stat = None

    # Additional convenience methods for MPRemotePath
    def chdir(self) -> MPRemotePath:
        "Set the current working directory on the board to this path." ""
        p = self.resolve()
        self.board.exec(f"os.chdir('{p}')")
        return p

    def copyfile(self, target: MPRemotePath | str) -> MPRemotePath:
        target = mpremotepath(target)
        if self.samefile(target):
            raise SameFileError(f"{self!s} and {target!s} are the same file")
        with self.board.raw_repl() as r:
            r.fs_cp(str(self), str(target))
        return target

    def copy(self, target: MPRemotePath | str) -> MPRemotePath:
        target = mpremotepath(target)
        target = target / self.name if target.is_dir() else target
        return self.copyfile(target)

    @classmethod
    def connect(
        cls,
        port: str | Board | SerialTransport,
        baud: int = 115200,
        wait: int = 0,
        *,
        set_clock: bool = False,
        utc: bool = False,
    ) -> None:
        """Connect to the micropython board on the given `port`.
        - `port` can be a `Board` instance, an mpremote `SerialTransport`
          instance or a string containing the full or abbreviated name of the
          serial port
        - `baud` is the baud rate to use for the serial connection
        - `wait` is the number of seconds to wait for the board to become
          available.
        - `set_clock` is a boolean indicating whether to synchronise the board
          clock with the host clock.
        - `utc` is a boolean indicating whether to use UTC for the board clock
        `baud` and `wait` are only used if `port` is a string.
        """
        cls.board = make_board(port, baud, wait, set_clock=set_clock, utc=utc)
        cls.board.exec(START_CODE)

    # Overrides for pathlib.Path methods
    @classmethod
    def cwd(cls) -> MPRemotePath:
        if not cls.board:
            raise ValueError("RemotePath.board must be set before use.")
        return cls(cls.board.eval("os.getcwd()"))

    @classmethod
    def home(cls) -> MPRemotePath:
        return cls("/")

    def samefile(self, other: Path | str) -> bool:
        if isinstance(other, str):
            other = MPRemotePath(other)
        return isinstance(other, MPRemotePath) and self.resolve() == other.resolve()

    def _from_direntry(self, entry: MPRemoteDirEntry) -> MPRemotePath:
        """Create a new `MPRemotePath` instance from a `MPRemoteDirEntry`
        object. The file `stat()` information from the `direntry` is cached in
        the new instance."""
        p = self._make_child_relpath(entry.name)  # type: ignore
        p._stat = entry.stat()
        return p

    def iterdir(self) -> Iterable[MPRemotePath]:
        with self._scandir() as it:
            return (self._from_direntry(f) for f in it)

    # `rglob()` calls `_scandir()` twice in a row for each dir, so cache the
    # results from the board.
    # TODO: replace with real caching.
    # @lru_cache(maxsize=1)
    def _ilistdir(self) -> Iterable[MPRemoteDirEntry]:
        """Return an iterable of `MPRemoteDirEntry` objects for the files in a
        directory on the micropython `board`."""
        # exec_eval() will return None if the directory is empty
        ls = self.board.exec_eval(f"_ils('{self}')") or tuple()
        return [MPRemoteDirEntry(str(self), name, *extra) for name, *extra in ls]

    # glob(), rglob() and walk() rely on _scandir()
    @contextmanager
    def _scandir(self) -> Generator[Iterable[MPRemoteDirEntry], None, None]:
        """Override for Path._scandir(): a context manager which produces an
        iterable of information about the files in a folder. This is used by
        `glob()` and `rglob()`."""
        yield self._ilistdir()

    def resolve(self, strict: bool = False) -> MPRemotePath:
        # The fs on the board has no concept of symlinks, so just eliminate ".."
        # and "." from the absolute path.
        parts = self._parts if self.is_absolute() else ([self.cwd()] + self._parts)
        new_parts = []
        for p in parts:
            if p == ".." and new_parts:
                new_parts.pop()
            elif p != ".":
                new_parts.append(p)
        p = self._from_parts(new_parts)  # type: ignore
        return p if p._parts != self._parts else self

    def stat(self) -> os.stat_result:
        if hasattr(self, "_stat") and self._stat is not None:
            return self._stat
        self._stat = self.board.fs_stat(str(self))
        return self._stat

    def owner(self) -> str:
        return "root"

    def group(self) -> str:
        return "root"

    def open(self, mode="r", buffering=-1, encoding=None, errors=None, newline=None):
        raise NotImplementedError

    def read_bytes(self) -> bytes:
        with self.board.raw_repl() as r:
            return r.fs_readfile(str(self))

    def read_text(self, encoding=None, errors=None) -> str:
        return self.read_bytes().decode(encoding or "utf-8", errors or "strict")

    def write_bytes(self, data: bytes) -> None:
        self._stat = None
        with self.board.raw_repl() as r:
            r.fs_writefile(str(self), data)

    def write_text(self, data, encoding=None, errors=None, newline=None):
        return self.write_bytes(data.encode(encoding or "utf-8", errors or "strict"))

    def readlink(self):
        raise NotImplementedError

    def touch(self, mode=0o666, exist_ok=True) -> None:
        self._stat = None
        with self.board.raw_repl() as r:
            r.fs_touch(str(self))

    def mkdir(self, mode=0o777, parents=False, exist_ok=False) -> None:
        self._stat = None
        with self.board.raw_repl() as r:
            r.fs_mkdir(str(self))

    def chmod(self, mode: int, *, follow_symlinks=True) -> None:
        raise NotImplementedError

    def lchmod(self, mode: int) -> None:
        raise NotImplementedError

    def unlink(self, missing_ok=False) -> None:
        self._stat = None
        with self.board.raw_repl() as r:
            r.fs_rm(str(self))

    def rmdir(self) -> None:
        self._stat = None
        with self.board.raw_repl() as r:
            r.fs_rmdir(str(self))

    def lstat(self) -> os.stat_result:
        return self.stat()

    def rename(self, target: Path | str) -> MPRemotePath:
        self.board.exec(f"os.rename('{self}','{target}')")
        target = mpremotepath(target)
        target._stat = self._stat
        self._stat = None
        return target

    def replace(self, target: Path | str) -> MPRemotePath:
        return self.rename(target)

    def symlink_to(
        self, target: MPRemotePath | str, target_is_directory: bool = False
    ) -> None:
        raise NotImplementedError

    def hardlink_to(self, target: MPRemotePath | str) -> None:
        raise NotImplementedError

    def link_to(self, target: MPRemotePath | str) -> None:
        raise NotImplementedError

    def exists(self) -> bool:
        try:
            self.stat()
        except FileNotFoundError:
            return False
        return True

    def is_dir(self) -> bool:
        return self.exists() and stat.S_ISDIR(self.stat().st_mode)

    def is_file(self) -> bool:
        return self.exists() and stat.S_ISREG(self.stat().st_mode)

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

    def expanduser(self) -> MPRemotePath:
        return (  # Interpret a leading "~/" as the root directory
            self._from_parts(["/"] + self._parts[1:])  # type: ignore
            if (not (self._drv or self._root) and self._parts[:1] == ["~"])
            else self
        )
