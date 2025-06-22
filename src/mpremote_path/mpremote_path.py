"""Provides the `MPRemotePath` class which provides a `pathlib.Path` compatible
interface to accessing and manipulating files on micropython boards via the
`mpremote` tool.
"""

# Copyright (c) 2021 @glenn20
# MIT License

# For python<3.10: Allow method type annotations to reference enclosing class
from __future__ import annotations

import io
import os
import stat
import sys
from pathlib import Path, PurePath, PurePosixPath, PureWindowsPath
from shutil import SameFileError
from typing import (
    IO,
    TYPE_CHECKING,
    Any,
    BinaryIO,
    Generator,
    Iterator,
    Literal,
    Union,
    cast,
    overload,
)

from mpremote.transport_serial import SerialTransport

from .board import Board

if TYPE_CHECKING:
    from _typeshed import (
        OpenBinaryMode,
        OpenBinaryModeReading,
        OpenBinaryModeUpdating,
        OpenBinaryModeWriting,
        OpenTextMode,
        ReadableBuffer,
        StrOrBytesPath,
    )

if sys.version_info >= (3, 10):
    PathType = os.PathLike[str]
else:
    PathType = PurePath


def mpremotepath(f: str | PathType) -> MPRemotePath:
    """If `f` is an `MPRemotePath` instance return it, else convert to
    `MPRemotePath` and return it."""
    return f if isinstance(f, MPRemotePath) else MPRemotePath(f)


def is_wildcard_pattern(pat: str) -> bool:
    """Whether this pattern needs actual matching using `glob()`, or can
    be looked up directly as a file."""
    return "*" in pat or "?" in pat or "[" in pat


class MPRemoteDirEntry:
    """A duck-typed version of `os.DirEntry` for use with `MPRemotePath`.

    Will be initialised from the results of calling `os.ilistdir()` on the
    micropython board. This is used to support the `iterdir()`, `_scandir()`,
    `glob()` and `rglob()` methods of `pathlib.Path` for `MPRemotePath`s."""

    __slots__ = ("parent", "name", "_stat", "_board")

    def __init__(
        self,
        board: Board,
        parent: str,
        name: str,
        mode: int = 0,
        inode: int = 0,
        size: int = 0,
        mtime: int = 0,
    ) -> None:
        self.name: str = name
        self.parent: str = parent
        self._board: Board = board
        self._stat: os.stat_result = os.stat_result(
            (mode, inode, 0, 0, 0, 0, size, mtime, mtime, mtime)
        )

    @property
    def path(self) -> str:
        return f"{self.parent.rstrip('/')}/{self.name}"

    def inode(self) -> int:
        return self._stat.st_ino

    def is_dir(self, *, follow_symlinks: bool = True) -> bool:
        return stat.S_ISDIR(self._stat.st_mode)

    def is_file(self, *, follow_symlinks: bool = True) -> bool:
        return stat.S_ISREG(self._stat.st_mode)

    def is_symlink(self) -> bool:
        return stat.S_ISLNK(self._stat.st_mode)

    def stat(self, *, follow_symlinks: bool = True) -> os.stat_result:
        if self._stat.st_size == 0:  # Get the full os.stat() result
            self._stat = self._board.fs_stat(self.path)
            if self._stat.st_mtime == 0:  # Fetch the mtime from the board
                mtime = self._board.eval(f"os.stat({self.path!r})[8]")
                self._stat = os.stat_result(self._stat[:7] + (mtime, mtime, mtime))
        return self._stat


# Path.glob(), Path.rglob(), Path.walk() and Path.iterdir() rely on _scandir()
# Can't use @contextmanager decorator because it doesn't work with broken
# pathlib.rglob()/walk() on python 3.12.
class MPRemoteScanDir:
    def __init__(self, board: Board, path: str):
        #  Wrap all the file ops in a single raw repl
        with board.raw_repl():
            files = cast(
                tuple[tuple[str]],
                board.exec_eval(f"for f in os.ilistdir('{path}'):print(f, end=',')")
                or tuple(),
            )
            self.result = (MPRemoteDirEntry(board, path, *f) for f in files)

    def __enter__(self) -> MPRemoteScanDir:
        return self

    def __exit__(self, *_exc: Any) -> None:
        pass

    def __iter__(self) -> Iterator[MPRemoteDirEntry]:
        return self.result


if hasattr(Path, "_accessor"):
    # For python<=3.9: Override accessor class to handle micropython paths
    from pathlib import _NormalAccessor  # type: ignore

    class _MPRemoteAccessor(_NormalAccessor):  # type: ignore
        @staticmethod
        def stat(path: str) -> os.stat_result:
            return MPRemotePath.board.fs_stat(path)

        @staticmethod
        def lstat(path: str) -> os.stat_result:
            return MPRemotePath.board.fs_stat(path)

        @staticmethod
        def listdir(path: str) -> list[str]:
            path = PureWindowsPath(path).as_posix() if os.name == "nt" else path
            return [p.name for p in MPRemoteScanDir(MPRemotePath.board, path)]

        @staticmethod
        def scandir(path: str) -> MPRemoteScanDir:
            path = PureWindowsPath(path).as_posix() if os.name == "nt" else path
            return MPRemoteScanDir(MPRemotePath.board, path)

    _mpremote_accessor = _MPRemoteAccessor()


if sys.version_info >= (3, 13):
    # For python>=3.13: Override globber class to handle micropython paths
    from glob import _StringGlobber  #  type: ignore

    class _MPRemoteGlobber(_StringGlobber):  #  type: ignore
        @staticmethod
        def lstat(path: str) -> os.stat_result:
            return MPRemotePath.board.fs_stat(path)

        @staticmethod
        def scandir(path: str) -> MPRemoteScanDir:
            path = PureWindowsPath(path).as_posix() if os.name == "nt" else path
            return MPRemoteScanDir(MPRemotePath.board, path)


class MPRemotePathWriter(io.BytesIO):
    """File object that flushes its contents to a micropython file on close.
    Returned by MPRemotePath.open(mode="w").
    """

    def __init__(self, board: Board, path: str):
        super().__init__()
        self.board: Board = board
        self.path: str = path

    def close(self) -> None:
        with self.board.raw_repl() as r:
            r.fs_writefile(self.path, self.getvalue())
        super().close()


# Paths on the board are always Posix paths even if local host is Windows.
class MPRemotePath(Path, PurePosixPath):
    "A `pathlib.Path` compatible class to hold details of files on the board."

    # __slots__ = ("_stat", "board")
    board: Board
    _stat: os.stat_result | None
    _drv: str  # Declare types for properties inherited from pathlib classes
    _root: str
    _parts: list[str]
    _home_dir: str = ""  # Home directory on the board, set by connect()

    if sys.version_info >= (3, 13):
        _globber = _MPRemoteGlobber

    def __init__(self, *args: str | PathType) -> None:
        if not self.__class__.board:
            raise ValueError("Must call MPRemotePath.connect() before use.")
        self.board = self.__class__.board
        self._stat = None
        if hasattr(self, "_from_parts"):
            super().__init__()
        else:
            super().__init__(*args)
        if hasattr(Path, "_accessor"):
            self._accessor = _mpremote_accessor  # For python<=3.9

    def __new__(cls, *args: str | PathType) -> MPRemotePath:
        if not cls.board:
            raise ValueError("Must call MPRemotePath.connect() before use.")
        if hasattr(cls, "_from_parts"):
            self = cast(MPRemotePath, getattr(cls, "_from_parts")(args))
        else:
            self = super().__new__(cls, *args)
        return self

    def with_segments(self, *pathsegments: str | PathType) -> MPRemotePath:
        return MPRemotePath(*pathsegments)

    # Additional convenience methods for MPRemotePath
    @classmethod
    def connect(
        cls,
        port: str | Board | SerialTransport,
        *,
        baud: int = 0,
        wait: int = 0,
        set_clock: bool = True,
        utc: bool = False,
    ) -> None:
        """Connect to the micropython board on the given `port`.
        - `port` can be a string containing the full or abbreviated name of the
          serial port, a Board instance or an mpremote `SerialTransport` instance.
        - `baud` is the baud rate to use for the serial connection
        - `wait` is the number of seconds to wait for the board to become
          available.
        - `set_clock` is a boolean indicating whether to synchronise the board
          clock with the host clock.
        - `utc` is a boolean indicating whether to use UTC for the board clock.

        `baud` and `wait` are only used if `port` is a string.
        """
        cls.board = (
            port if isinstance(port, Board) else
            Board(port, baud=baud, wait=wait)
        )  # fmt: skip
        cls.board.check_clock(set_clock, utc)
        cls.board.exec("import os")
        # Set the home directory to the initial working directory on the board.
        # On devices, this will be the root directory.
        # On the micropython unix port it will be dir where the script is run.
        cls._home_dir = cls.board.eval_str("os.getcwd()")

    @classmethod
    def disconnect(cls) -> None:
        """Disconnect from the micropython board."""
        if cls.board:
            cls.board.close()

    def chdir(self) -> MPRemotePath:
        "Set the current working directory on the board to this path."
        p = self.resolve()
        self.board.exec(f"os.chdir('{p.as_posix()}')")
        return p

    def copyfile(self, target: MPRemotePath | str) -> MPRemotePath:
        target = mpremotepath(target)
        if self.samefile(target):
            raise SameFileError(f"{self!s} and {target!s} are the same file")
        target.write_bytes(self.read_bytes())
        return target

    def copy(self, target: MPRemotePath | str) -> MPRemotePath:
        target = mpremotepath(target)
        target = target / self.name if target.is_dir() else target
        return self.copyfile(target)

    @classmethod
    def cwd(cls) -> MPRemotePath:
        if not cls.board:
            raise ValueError("RemotePath.board must be set before use.")
        return cls(cls.board.eval("os.getcwd()"))

    # Overrides for pathlib.Path methods
    @classmethod
    def home(cls) -> MPRemotePath:
        return cls(cls._home_dir)

    # Path.glob(), Path.rglob(), Path.walk() and Path.iterdir() rely on _scandir()
    def _scandir(self) -> MPRemoteScanDir:
        """Override for Path._scandir(): returns a context manager which produces an
        iterable of information about the files in a folder. This is used by
        `glob()`, `rglob()` and `walk()`."""
        return MPRemoteScanDir(self.board, str(self))

    def _from_direntry(self, entry: MPRemoteDirEntry) -> MPRemotePath:
        """Create a new `MPRemotePath` instance from a `MPRemoteDirEntry`
        object. The file `stat()` information from the `direntry` is cached in
        the new instance."""
        p = MPRemotePath(str(self), entry.name)
        p.board = self.board
        p._stat = entry.stat()
        return p

    def iterdir(self) -> Generator[MPRemotePath, None, None]:
        with self._scandir() as it:
            return (self._from_direntry(f) for f in it)

    def absolute(self) -> MPRemotePath:
        return self if self.is_absolute() else self.cwd() / self

    def resolve(self, strict: bool = False) -> MPRemotePath:
        # The fs on the board has no concept of symlinks, so just eliminate ".."
        # and "." from the absolute path.
        is_abs = self.is_absolute()
        parts = self.parts if is_abs else (self.cwd().parts + self.parts)
        new_parts: list[str] = []
        for p in parts:
            if p == ".." and new_parts:
                new_parts.pop()
            elif p != ".":
                new_parts.append(p)
        return (
            self if is_abs and new_parts == list(parts) else
            self.with_segments(*new_parts)
        )  # fmt: skip

    def samefile(self, other_path: Union[str, os.PathLike[str]]) -> bool:
        if isinstance(other_path, str):
            other_path = MPRemotePath(other_path)
        return (
            isinstance(other_path, MPRemotePath)
            and self.resolve() == other_path.resolve()
        )

    def stat(self, *, follow_symlinks: bool = False) -> os.stat_result:
        if hasattr(self, "_stat") and self._stat is not None:
            return self._stat
        stat = self.board.fs_stat(str(self))
        self._stat = stat
        return stat

    def owner(self, *, follow_symlinks: bool = False) -> str:
        return "root"

    def group(self, *, follow_symlinks: bool = False) -> str:
        return "root"

    @overload
    def open(
        self,
        mode: OpenTextMode = "r",
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> io.TextIOWrapper: ...

    # Unbuffered binary mode: returns a FileIO
    @overload
    def open(
        self,
        mode: OpenBinaryMode,
        buffering: Literal[0],
        encoding: None = None,
        errors: None = None,
        newline: None = None,
    ) -> io.FileIO: ...

    # Buffering is on: return BufferedRandom, BufferedReader, or BufferedWriter
    @overload
    def open(
        self,
        mode: OpenBinaryModeUpdating,
        buffering: Literal[-1, 1] = -1,
        encoding: None = None,
        errors: None = None,
        newline: None = None,
    ) -> io.BufferedRandom: ...
    @overload
    def open(
        self,
        mode: OpenBinaryModeWriting,
        buffering: Literal[-1, 1] = -1,
        encoding: None = None,
        errors: None = None,
        newline: None = None,
    ) -> io.BufferedWriter: ...
    @overload
    def open(
        self,
        mode: OpenBinaryModeReading,
        buffering: Literal[-1, 1] = -1,
        encoding: None = None,
        errors: None = None,
        newline: None = None,
    ) -> io.BufferedReader: ...

    # Buffering cannot be determined: fall back to BinaryIO
    @overload
    def open(
        self,
        mode: OpenBinaryMode,
        buffering: int = -1,
        encoding: None = None,
        errors: None = None,
        newline: None = None,
    ) -> BinaryIO: ...

    # Fallback if mode is not specified
    @overload
    def open(
        self,
        mode: str,
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> IO[Any]: ...

    def open(  #  type: ignore
        self,
        mode: str = "r",
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> IO[Any]:
        """Open the micropython file pointed by this path and return a file
        object, similar to the built-in open() function.
        """
        if buffering != -1:
            raise io.UnsupportedOperation()
        action = "".join(c for c in mode if c not in "btU")
        if action == "r":
            with self.board.raw_repl() as r:
                fileobj = io.BytesIO(r.fs_readfile(str(self.resolve())))
        elif action == "w":
            fileobj = MPRemotePathWriter(self.board, str(self.resolve()))
        else:
            raise io.UnsupportedOperation()
        if "b" not in mode:
            return io.TextIOWrapper(fileobj, encoding, errors, newline)
        return fileobj

    def read_bytes(self) -> bytes:
        with self.board.raw_repl() as r:
            return r.fs_readfile(str(self))

    def read_text(
        self,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> str:
        return self.read_bytes().decode(encoding or "utf-8", errors or "strict")

    def write_bytes(self, data: ReadableBuffer) -> int:
        self._stat = None
        buf = bytes(data)
        with self.board.raw_repl() as r:
            r.fs_writefile(str(self), buf)
        return len(buf)

    def write_text(
        self,
        data: str,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> int:
        return self.write_bytes(data.encode(encoding or "utf-8", errors or "strict"))

    def readlink(self) -> MPRemotePath:
        raise NotImplementedError

    def touch(self, mode: int = 0o666, exist_ok: bool = True) -> None:
        self._stat = None
        with self.board.raw_repl() as r:
            if hasattr(r, "fs_touchfile"):
                r.fs_touchfile(str(self))  # mpremote >= 1.24.0
            else:
                r.fs_touch(str(self))

    def mkdir(
        self, mode: int = 0o777, parents: bool = False, exist_ok: bool = False
    ) -> None:
        self._stat = None
        with self.board.raw_repl() as r:
            try:
                r.fs_mkdir(str(self))
            except FileExistsError:
                if not exist_ok:
                    raise
            except FileNotFoundError:
                if not parents:
                    raise
                self.parent.mkdir(parents=True, exist_ok=True)
                r.fs_mkdir(str(self))

    def chmod(self, mode: int, *, follow_symlinks: bool = True) -> None:
        raise NotImplementedError

    def lchmod(self, mode: int) -> None:
        raise NotImplementedError

    def unlink(self, missing_ok: bool = False) -> None:
        self._stat = None
        with self.board.raw_repl() as r:
            if hasattr(r, "fs_rmfile"):
                r.fs_rmfile(str(self))  # mpremote >= 1.24.0
            else:
                r.fs_rm(str(self))

    def rmdir(self) -> None:
        self._stat = None
        with self.board.raw_repl() as r:
            r.fs_rmdir(str(self))

    def lstat(self) -> os.stat_result:
        return self.stat()

    def rename(self, target: str | PathType) -> MPRemotePath:
        self.board.exec(f"os.rename('{self}','{target}')")
        target = mpremotepath(target)
        target._stat = self._stat
        self._stat = None
        return target

    def replace(self, target: str | PathType) -> MPRemotePath:
        return self.rename(target)

    def symlink_to(  # type: ignore
        self, target: MPRemotePath | str, target_is_directory: bool = False
    ) -> None:
        raise NotImplementedError

    def hardlink_to(self, target: StrOrBytesPath) -> None:
        raise NotImplementedError

    def link_to(self, target: MPRemotePath | str) -> None:  # type: ignore
        raise NotImplementedError

    def exists(self, *, follow_symlinks: bool = False) -> bool:
        try:
            self.stat(follow_symlinks=follow_symlinks)
        except FileNotFoundError:
            return False
        return True

    def is_dir(self, *, follow_symlinks: bool = False) -> bool:
        return self.exists(follow_symlinks=follow_symlinks) and stat.S_ISDIR(
            self.stat(follow_symlinks=follow_symlinks).st_mode
        )

    def is_file(self, *, follow_symlinks: bool = False) -> bool:
        return self.exists(follow_symlinks=follow_symlinks) and stat.S_ISREG(
            self.stat(follow_symlinks=follow_symlinks).st_mode
        )

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
        first, rest = self.parts[:1], self.parts[1:]
        return self.with_segments(self._home_dir, *rest) if first == ("~",) else self
