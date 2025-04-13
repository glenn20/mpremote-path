"""A collection of file system utilities for use with `mpremote_path`.

Includes functions for copying, moving and removing multiple files and
directories locally, or on serial attached micropython boards.

These functions operate on files specified as `Path` or `MPath` instances. Use
the `mpfscmd` sub-module to operate on files specified as strings or lists of
strings.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Iterable, Optional, Tuple

from mpremote_path import MPRemotePath as MPath

# A directory and its contents: (directory, [file1, file2, ...])
Dirfiles = Tuple[Optional[Path], Iterable[Path]]
Dirlist = Iterable[Dirfiles]  # A list of directories and their contents

max_depth = 20  # Default maximum depth for recursive directory listings


def connect(*args: Any, **kwargs: Any) -> None:
    """Connect to a micropython board.
    The arguments are passed to `MPath.connect()`."""
    MPath.connect(*args, **kwargs)


def copyfile(src: Path, dst: Path) -> Path:
    """Copy a regular file, with optimisations for mpremote paths.
    `src` and `dst` can be either `Path` or `MPRemotePath` instances."""
    if not src.is_file():
        raise ValueError(f"'{src}' is not a regular file")
    elif isinstance(src, MPath) and isinstance(dst, MPath):
        src.copyfile(dst)  # Copy from micropython board to micropython board
    elif not isinstance(src, MPath) and not isinstance(dst, MPath):
        shutil.copyfile(src, dst)  # Copy local file to local file
    else:
        dst.write_bytes(src.read_bytes())  # Fall back to copying file content
    return dst


def copypath(src: Path, dst: Path) -> Path:
    """Copy a file or directory.
    If `src` is a regular file, call `copyfile()` to copy it to `dst`.
    If `src` is a directory, and `dst` is not a directory, make the new
    directory.
    Returns `dst` if successful, otherwise returns `None`."""
    if src.is_dir():
        print(f"{src}/ -> {dst}/")
        if not dst.is_dir():
            dst.mkdir()  # "Copy" by creating the destination directory
        return dst
    else:
        print(f"{src} -> {dst}")
        return copyfile(src, dst)


def rcopy(src: Path, dst: Path) -> None:
    """Copy a file or directory recursively."""
    if copypath(src, dst):
        if src.is_dir():
            for child in src.iterdir():
                rcopy(child, dst / child.name)


def copy(files: Iterable[Path], dest: Path) -> None:
    """Recursively copy files and directories from `files` to `dest`.
    If `dest` is an existing directory, move all files into it.
    If `dest` is not an existing directory and there is only one source `file`
    it will be copied to `dest`.
    Otherwise a `ValueError` is raised."""
    it = iter(files)
    if dest.is_dir():
        for f in it:
            rcopy(f, dest / f.name)
    elif (f := next(it, None)) and next(it, None) is None:  # type: ignore
        # If there is only one src `path`, make a copy called `dest`
        rcopy(f, dest)
    else:
        raise ValueError(f"%cp: Destination must be a directory: {dest!r}")


def move(files: Iterable[Path], dest: Path) -> None:
    """Move files and directories into the `dest` folder.
    If `dest` is an existing directory, move all files/dirs into it.
    If `dest` is not an existing directory and there is only one source `path`
    it will be renamed to `dest`.
    Otherwise a `ValueError` is raised.
    """
    it = iter(files)
    if dest.is_dir():  # Move all files into the dest directory
        for src in it:
            dst = dest / src.name
            slash = "/" if src.is_dir() else ""
            print(f"{src}{slash} -> {dst}{slash}")
            src.rename(dst)
    elif (src := next(it, None)) is not None and next(it, None) is None:  # type: ignore
        # If there is only one src `path`, rename it to `dest`
        slash = "/" if src.is_dir() else ""
        print(f"{src}{slash} -> {dest}{slash}")
        src.rename(dest)
    else:
        raise ValueError(f"%mv: Destination is not a directory: {dest!r}")


def remove(files: Iterable[Path], recursive: bool = False) -> None:
    """Remove (delete) files (and directories if `recursive` is `True`)."""
    for f in files:
        if f.is_file():
            print(f"{str(f)}")
            f.unlink()
        elif f.is_dir():
            if recursive:
                remove(f.iterdir(), recursive)
                print(f"{str(f)}/")
                f.rmdir()
            else:
                print(
                    f"Skipping '{str(f)}/' (use `recursive=True` to delete directories)"
                )


def cwd() -> MPath:
    """Get the working directory on the micropython board."""
    return MPath.cwd()


def walk(path: Path, depth: int = max_depth) -> Dirlist:
    """Return a directory list of `path` (must be directory) up to `depth` deep.
    If `depth` is 0, only the top level directory is listed."""
    if path.is_dir():
        files = sorted(path.iterdir())
        yield (path, files)
        if depth > 0:
            for child in (f for f in files if f.is_dir()):
                yield from walk(child, depth - 1)


def walk_files(files: Iterable[Path], recursive: bool = False) -> Dirlist:
    """Return a directory list of all `files`, which may be regular files or
    directories. If `recursive` is `True`, list all files in subdirectories
    recursively."""
    files = sorted(files)
    dirs = [f for f in files if f.is_dir()]
    if not recursive and len(dirs) == len(files) == 1:
        # If only one directory in list, just list the files in that directory
        _dir, files = next(iter(walk(dirs[0], 0)))
        yield (None, files)
        return
    yield (None, [f for f in files if not f.is_dir()])
    for f in dirs:
        yield from walk(f, max_depth if recursive else 0)


def skip_file(src: Path, dst: Path) -> bool:
    "If local is not newer than remote, return True."
    s, d = src.stat(), dst.stat()
    return (src.is_dir() and dst.is_dir()) or (
        src.is_file()
        and dst.is_file()
        and round((d := dst.stat()).st_mtime) >= round((s := src.stat()).st_mtime)
        and d.st_size == s.st_size
    )


def check_files(
    cmd: str, files: Iterable[Path], dest: Path | None = None, opts: str = ""
) -> tuple[list[Path], Path | None]:
    filelist = list(files)
    missing = [str(f) for f in filelist if not f.exists()]
    dirs = [str(d) + "/" for d in filelist if d.is_dir()]
    # Check for invalid requests
    if missing:
        print(f"%{cmd}: Error: Missing files: {missing}.")
        return ([], None)
    if dest:
        for f in filelist:
            if f.is_dir() and f in dest.parents:
                print(f"%{cmd}: Error: {dest!r} is subfolder of {f!r}")
                return ([], None)
            if str(f) == str(dest):
                print(f"%{cmd}: Error: source is same as dest: {f!r}")
                return ([], None)
    if dirs and cmd in ["rm", "cp", "get", "put"] and "r" not in opts:
        print(f'%{cmd}: Error: Can not process dirs (use "{cmd} -r"): {dirs}')
        return ([], None)

    return (filelist, dest)
