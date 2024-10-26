"""Functions to manipulate files on a micropython board.

These functions accept files specified as strings or lists of strings and
use the `mpremote_path.util.fs` module to perform the operations on the
micropython board.

Includes functions for copying, moving and removing multiple files and
directories on micropython boards and for printing listings of files and
directories.
"""

from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import Any, Callable, Iterable, Tuple, Union

from mpremote_path import MPRemotePath as MPath
from mpremote_path import is_wildcard_pattern, mpremotepath
from mpremote_path.util import mpfsops

# A list of files and/or directories: [file1, file2, ...]
FileList = Union[Iterable[Union[Path, str]], Path, str]
# A directory and its contents: (directory, [file1, file2, ...])
Dirfiles = Tuple[Union[Path, None], Iterable[Path]]
Dirlist = Iterable[Dirfiles]  # A list of directories and their contents


# Functions to format the filenames printed by `ls()`.
def default_name_formatter(path: Path) -> str:
    return path.name or str(path)


def default_path_formatter(path: Path) -> str:
    return str(path)


# Override these to colourise the filenames.
name_formatter: Callable[[Path], str] = default_name_formatter

path_formatter: Callable[[Path], str] = default_path_formatter


def local_path(path: Path | str, cls: type[Path] = Path) -> Path:
    """If `path` is a string, return a `Path` instance (`MPath` if it starts
    with `:`)."""
    return (
        path
        if isinstance(path, Path)
        else MPath(path[1:])
        if path.startswith(":")
        else cls(path)
    )


def path_list(files: FileList, cls: type[Path] = Path) -> Iterable[Path]:
    """A convenience function for creating a list of `Path` instances.
    - `files` contains the files/directories to print, which may be:
        - `Iterable[Path|MPath|str]`: a list of files/directories,
        - `Path` (or `MPath`): a single file/dir, or
        - `str`: the name of a single file.
    - `cls`: the class to use for the `Path` instances (default: `Path`).

    `str` values in the list will be converted to instances of `cls` and may
    include filename globbing wildcard characters: `*`, `?`, `[xyz]`, `[!xyz]`
    or `**`."""
    filelist: Iterable[Path | str] = (
        (files,) if isinstance(files, str) or isinstance(files, Path) else files
    )
    cwd = cls.cwd()  # Current directory: for globbing if required
    for f in filelist:
        if isinstance(f, str) and is_wildcard_pattern(f):
            # Expand glob pattern and yield each file
            yield from (list(cwd.glob(f)) or [cls(f)])
        else:
            # Yield the next file - convert to cls if necessary
            yield f if isinstance(f, cls) else cls(f)


def local_path_list(files: FileList) -> Iterable[Path]:
    return path_list(files, Path)


def remote_path_list(files: FileList) -> Iterable[Path]:
    return path_list(files, MPath)


def slashify(path: Path | str) -> str:
    """Return `path` as a string (with a trailing slash if it is a directory)."""
    s = str(path)
    add_slash = not s.endswith("/") and isinstance(path, Path) and path.is_dir()
    return s + "/" if add_slash else s


def ls_long(dirlist: Dirlist) -> None:
    """Print a long-style file listing from a `Dirlist`."""
    for directory, files in dirlist:
        if directory:
            print(f"{path_formatter(directory)}:")
        else:
            for f in (f for f in files if not f.exists()):
                print(f"'{f}': No such file or directory")
        for f in files:
            st = f.stat()
            size = st.st_size if not f.is_dir() else 0
            t = time.strftime("%c", time.localtime(st.st_mtime)).replace(" 0", "  ")
            print(f"{size:9d} {t[:-3]} {name_formatter(f)}")


def ls_short(dirlist: Dirlist) -> None:
    """Print a short-style file listing from a `Dirlist`."""
    started = False
    columns = shutil.get_terminal_size().columns
    for directory, files in dirlist:
        files = list(files)
        if started:
            print()  # Add a blank line between directory listings
        if directory:
            print(f"{path_formatter(directory)}:")
            started = True
        else:
            for f in (f for f in files if not f.exists()):
                print(f"'{f}': No such file or directory")
            files = [f for f in files if f.exists()]
        if not files:
            pass
        elif len(files) < 20 and sum(len(f.name) + 2 for f in files) < columns:
            # Print all on one line
            print("  ".join(name_formatter(f) for f in files))
            started = True
        else:
            # Print in columns - by row
            w = max(len(f.name) for f in files) + 2
            spaces = " " * (w - 1)
            cols = columns // w
            for i, f in enumerate(files, start=1):
                print(name_formatter(f), spaces[len(f.name) :], end="")
                if i % cols == 0 or i == len(files):
                    print()
                started = True


def ls(
    files: FileList = ".",
    long_style: bool = False,
    recursive: bool = False,
) -> None:
    """Print a file listing from `files`.
    - `files` contains the files/directories to print, which may be:
      - `Iterable[MPath|Path|str]`: a list of files/directories,
      - `Path` (including `MPath`): a single file/dir to list, or
      - `str`: containing a whitespace separated list of files/dirs.
    - `long_listing`: if `True`, print a long-style file listing.
    - `recursive`: if `True`, print files in subdirectories.

    `str` values may include filename globbing wildcard characters: `*`, `?`,
    `[xyz]`, `[!xyz]` or `**`."""
    dirlist = mpfsops.walk_files(remote_path_list(files or "."), recursive)
    ls_func = ls_long if long_style else ls_short
    ls_func(dirlist)


def get(files: FileList, dest: Path | str) -> Path:
    """Get files and directories from the micropython board.
    `dest` must be an existing directory."""
    p = local_path(dest)
    mpfsops.copy(remote_path_list(files), p)
    return p


def put(files: FileList, dest: Path | str) -> MPath:
    """Get files and directories from the micropython board.
    `dest` must be an existing directory."""
    p = mpremotepath(dest)
    mpfsops.copy(local_path_list(files), p)
    return p


def cp(files: FileList, dest: Path | str) -> MPath:
    """Copy files and directories from `files` to `dest` on the micropython board.
    If `dest` is an existing directory, move all files into it.
    If `dest` is not an existing directory and there is only one source `file`
    it will be renamed to `dest`.
    Otherwise a `ValueError` is raised."""
    p = mpremotepath(dest)
    mpfsops.copy(remote_path_list(files), p)
    return p


def mv(files: FileList, dest: Path | str) -> MPath:
    """Implement the `mv` command to move/rename files and directories.
    If `dest` is an existing directory, move all files/dirs into it.
    If `dest` is not an existing directory and there is only one source `path`
    it will be renamed to `dest`.
    Otherwise a `ValueError` is raised.
    """
    p = mpremotepath(dest)
    mpfsops.move(remote_path_list(files), p)
    return p


def rm(files: FileList, recursive: bool = False) -> None:
    """Remove (delete) files (and directories if `recursive` is `True`)."""
    mpfsops.remove(remote_path_list(files), recursive)


def cat(files: FileList) -> None:
    for p in remote_path_list(files):
        if p.is_file():
            print(p.read_text())
        elif p.is_dir():
            print(f"Error: '{p.as_posix()}': is a directory.")
        else:
            print(f"Error: '{p.as_posix()}': can not open.")


def touch(name: str) -> MPath:
    """Create or update timestamp on a file on the micropython board."""
    p = mpremotepath(name)
    p.touch()
    return p


def mkdir(name: str) -> MPath:
    """Create a directory on the micropython board."""
    p = mpremotepath(name)
    p.mkdir()
    return p


def rmdir(name: str) -> MPath:
    """Delete a directory on the micropython board."""
    p = mpremotepath(name)
    p.rmdir()
    return p


def cd(name: str) -> MPath:
    """Set the working directory on the micropython board."""
    p = mpremotepath(name).resolve()
    p.chdir()
    return p


def cwd() -> MPath:
    """Get the working directory on the micropython board."""
    return MPath.cwd()


def connect(*args: Any, **kwargs: Any) -> None:
    """Connect to a micropython board.
    The arguments are passed to `MPath.connect()`."""
    MPath.connect(*args, **kwargs)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Manipulate files on a micropython board.",
        usage=(
            "%(prog)s command [options] [files] [destination]"
            "  command: ls, mkdir, rmdir, cd, cwd, pwd, touch, rm, cp, mv, put, get"
            "  options: -l (long listing), -r (recursive)"
        ),
    )
    parser.add_argument(
        "-r", "--recursive", help="operate recursively on dirs", action="store_true"
    )
    parser.add_argument(
        "-l", "--long", help="use a long listing format", action="store_true"
    )
    parser.add_argument(
        "-p", "--port", help="serial port for micropython board", default="u0"
    )
    parser.add_argument("cmd", help="command to execute")
    parser.add_argument("args", help="filenames and destination", nargs="*")
    args = parser.parse_args()
    src, dst = (args.args[0], args.args[1]) if len(args.args) > 1 else ("", "")

    connect(args.port)

    if args.cmd == "ls":
        ls(args.args, args.long, args.recursive)
    elif args.cmd == "cat":
        cat(args.args)
    elif args.cmd == "mkdir":
        mkdir(args.args[0])
    elif args.cmd == "rmdir":
        rmdir(args.args[0])
    elif args.cmd == "cd":
        cd(args.args[0])
    elif args.cmd in ("cwd", "pwd"):
        print(cwd().as_posix())
    elif args.cmd == "touch":
        touch(args.args[0])
    elif args.cmd == "rm":
        rm(args.args, args.recursive)
    elif args.cmd == "cp":
        cp(src, dst)
    elif args.cmd == "mv":
        mv(src, dst)
    elif args.cmd == "put":
        put(src, dst)
    elif args.cmd == "get":
        get(src, dst)
    return 0


if __name__ == "__main__":
    main()
