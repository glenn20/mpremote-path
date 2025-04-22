# `mpremote_path` - a pathlib interface for files on micropython boards

[![PyPI](
  https://img.shields.io/pypi/v/mpremote-path)](
  https://pypi.org/project/mpremote-path)
[![PyPI Supported Python Versions](
  https://img.shields.io/pypi/pyversions/mpremote-path.svg)](
  https://pypi.python.org/pypi/mpremote-path/)
[![GitHub Actions (Tests)](
  https://github.com/glenn20/mpremote-path/actions/workflows/ci-test-build.yaml/badge.svg)](
  https://github.com/glenn20/mpremote-path/actions/workflows/ci-test-build.yaml)
[![GitHub Actions (Publish)](
  https://github.com/glenn20/mpremote-path/actions/workflows/ci-release.yaml/badge.svg)](
  https://github.com/glenn20/mpremote-path/actions/workflows/ci-release.yaml)
[![PyPI - License](
  https://img.shields.io/pypi/l/mpremote-path)](
  https://opensource.org/licenses/MIT)
[![pre-commit](
  https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](
  https://github.com/pre-commit/pre-commit)

Provides a convenient,
[`pathlib`](https://docs.python.org/3/library/pathlib.html) compatible python
interface to access and manipulate files on a serial-attached
[micropython](https://github.com/micropython/micropython) board from the host
computer. **mpremote-path** provides the `MPRemotePath` class which implements a
`pathlib.Path` compatible interface to the file access features of the
[mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html) tool.
Tested on Linux, Windows and MacOS.

**Contents:**

**[`mpremote_path`](#features) module:
  [Features](#features) |
  [Installation](#installation) |
  [API Docs](#api-docs-mpremote_path-module)**

- A module providing `pathlib`-like access to files on a serial-attached
  micropython board from a host computer.

**[`mpremote_path.util.mpfs`](#mpremote_pathutilmpfs-module) module:
  [Features](#mpfs-features) |
  [API Docs - Functions](#mpremote_pathutilmpfs-functions)**

- Provides convenience methods for working with files using the `mpremotepath`
  module. Includes the `mpfs` command line utility for managing files on a
  serial-attached micropython board.

**[`mpremote_path.util.mpfsops`](#mpremote_pathutilmpfsops-module) module:
  [Features](#mpfsops-features) |
  [API Docs - Functions](#mpremote_pathutilmpfsops-functions)**

## Features

Provides the `MPRemotePath` class:

- implements methods to access and manipulate files on micropython boards
  following  the familiar `pathlib.Path` interface:

```py
from mpremote_path import MPRemotePath as MPath

MPath.connect("u0")                 # Use device attached to /dev/ttyUSB0
p = MPath("/main.py")
print(p.read_text())                # Print out contents of /main.py

root = MPath("/")
q = root / "temp.txt"
q.write_bytes(b"Hello World\n")     # Create "/temp.txt"
print(q.read_bytes())               # Print out contents of /temp.txt
q.unlink()                          # Delete temp.txt

d = MPath("/data")
d.mkdir()                           # Create a new directory /data
d.chdir()                           # Set the working directory to /data
root.chdir()                        # Set the working directory to /
d.rmdir()                           # Delete /data
print([str(f) for f in MPath("/lib").rglob("*.py")])  # Print name of all python files in subdirs of /lib
```

- inherits from `pathlib.PosixPath` class, so code which works on `Path` objects will
  also work transparently on `MPRemotePath` objects, eg:

```py
from pathlib import Path
from mpremote_path import MPRemotePath as MPath

# Recursively copy files and subdirectories from src to dst
def rcopy(src: Path, dst: Path) -> None:
    if src.is_dir():
        print(f"{src}/ -> {dst}/")
        dst.mkdir()
        for child in src.iterdir():
            rcopy(child, dst / child.name)
    elif src.is_file():
        print(f"{src} -> {dst}")
        dst.write_bytes(src.read_bytes())

MPath.connect("u0")               # Use device attached to /dev/ttyUSB0

# Make a local copy of a directory on the host computer
rcopy(Path("app"), Path("../app-backup"))

# Copy local directory from computer to serial-attached micropython board
rcopy(Path("app"), MPath("/lib/app"))

# Copy a directory from the micropython board to the local disk
rcopy(MPath("/lib"), Path("./lib2"))
```

## Installation

If you use a python virtual environment (recommended), make sure it is active.

### Install from PYPI

- Using pip: `pip install mpremote-path`, or
- Using uv: `uv pip install mpremote-path`.

### Install from github source

I recommend using uv to install and manage dependencies and dev environments.

```bash
git clone https://github.com/glenn20/mpremote-path
cd mpremote-path
uv build  # To build an installable .whl file
uv tool install dist/mpremote-path-0.1.4-py3-none-any.whl
```

*Optional*: Run the test suite with: `uv run pytest` or `uv run tox`.

- Warning: running these tests will create and delete files and subdirectories
in a new folder on the micropython board: `/_tests`.

```bash
pytest -v --port=/dev/ttyUSB0
============================= test session starts ==============================
platform linux -- Python 3.11.2, pytest-7.4.3, pluggy-1.3.0 --
configfile: pyproject.toml
plugins: anyio-4.0.0
collected 11 items

tests/test_base.py::test_root_folder PASSED                              [  9%]
tests/test_base.py::test_mkdir PASSED                                    [ 18%]
tests/test_base.py::test_cd PASSED                                       [ 27%]
tests/test_base.py::test_touch_unlink PASSED                             [ 36%]
tests/test_base.py::test_read_write_bytes PASSED                         [ 45%]
tests/test_base.py::test_read_write_text PASSED                          [ 54%]
tests/test_base.py::test_resolve PASSED                                  [ 63%]
tests/test_base.py::test_not_implemented PASSED                          [ 72%]
tests/test_recursive_copy.py::test_recursive_copy PASSED                 [ 81%]
tests/test_recursive_copy.py::test_glob_rglob PASSED                     [ 90%]
tests/test_recursive_copy.py::test_recursive_rm PASSED                   [100%]

============================= 11 passed in 27.68s ==============================
```

## API docs: `mpremote_path` module

### Class `MPRemotePath`

- Class **`MPRemotePath(*pathsegments)`**

  - Create an MPRemotePath instance representing the pathname for a file on a
    micropython board. The file may or may not exist on the board and may be a
    regular file or a directory. If the file does not exist, it can be created
    with the `touch()`, `mkdir()`, `write_bytes()` or `write_text()` methods.

    The file pathname is built up by concatenating the `pathsegments` provided
    as arguments. The segments may be strings or `Path` objects (including
    `MPRemotePath`). (See [`pathlib.Path`](
    https://docs.python.org/3/library/pathlib.html#pathlib.Path))

#### Additional methods (not present in ordinary `Path` instances)

- Classmethod: **`connect(port: str | Board | SerialTransport) -> None`**

  - Establish a connection to the serial-attached micropython board. `port` may
    be of type:
    - `str`: the name of a serial port (full or abbreviated), eg:
      `"/dev/ttyUSB0"` or `"u0"`,
    - `SerialTransport`: the
      [mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html)
      interface to the micropython board, or
    - `mpremote_path.Board`: a wrapper for the `SerialTransport` interface.

    This method must be called before any methods that attempt to interact with
    the micropython board.

- Method: **`chdir() -> MPRemotePath`**

  - Set the working directory on the board to the path, which must be an
    existing directory. This is provided as a convenience to simplify changing
    the working directory on the board. Returns the new working directory as a
    normalised absolute path. This is an `MPRemotePath`-only extension.

- Method: **`copyfile(target: MPRemotePath | str) -> MPRemotePath`**

  - Make a copy (named `target`) of a file on the micropython board. `target`
    may be the name of the target file (`str`) or another `MPRemotePath`
    instance. This provides the equivalent of `os.copyfile()` for files on the
    micropython board.

- Method: **`copy(target: MPRemotePath | str) -> MPRemotePath`**

  - Make a copy (named `target`) of the file or directory. If the source object
    is a directory, create a new directory called `target`. If the source object
    is a regular file, make a copy with `copyfile(target)`.

#### Inherited Properties, Methods and Operators

- From
  [pathlib.PurePath](https://docs.python.org/3/library/pathlib.html#pathlib.PurePath):

  - *Properties*:
    - `parts`, `drive`, `root`, `anchor`, `parents`, `parent`, `name`, `suffix`,
      `suffixes`, `stem`
  - *Methods*:
    - `as_posix()`, `as_uri()`, `is_absolute()`, `is_relative_to(other)`,
      `is_reserved()`, `joinpath(*pathsegments)`, `match(pattern)`,
      `relative_to()`, `with_name(name)`, `with_stem(stem)`, `with_suffix()`,
      `with_segments(*pathsegments)`
  - *Operators*:
    - `/`: the slash operator concatenates path segments to create child paths,
      - eg. `lib = MPRemotePath("/lib"); pkg_dir = lib / "pkg"`.

- Inherits or overrides from
  [pathlib.Path](https://docs.python.org/3/library/pathlib.html#pathlib.Path):

  - *Methods*:
    - `cwd()`, `home()`, `stat()`, `exists()`, `expanduser()`, `glob(pattern)`,
      `group()`, `is_dir()`, `is_file()`, `is_junction()`, `is_mount()`,
      `samefile(other)`, `is_symlink()`, `is_socket()`, `is_fifo()`,
      `is_block_device()`, `is_char_device()`, `iterdir()`, `walk()`, `lstat()`,
      `mkdir()`, `owner()`, `open()`, `read_bytes()`, `read_text()`,
      `rename(target)`, `replace(target)`, `absolute()`, `resolve()`,
      `rglob(pattern)`, `rmdir()`, `touch()`, `unlink()`, `write_bytes(data)`,
      `write_text(text)`
  - *Will raise a `NotImplemented` exception*:
    - `chmod()`, `lchmod()`, `read_link()`, `symlimk_to(target)`,
      `hardlink_to(target)`

## `mpremote_path.util.mpfs` module

**WARNING: This API is a work-in-progress and subject to wholsesale change.**

### `mpfs` Features

Provides utility functions for working with files on a serial-attached
micropython board.

```py
from pathlib import Path
from mpremote_path import MPath
from mpremote_path.util import mpfs as fs

fs.connect("u0")                 # Use device attached to /dev/ttyUSB0

fs.mkdir("/app")
fs.put(["app/data", "app/*.py"], "/app") # Copy app files to the board
fs.get("/app/data/*", "./backup/data")  # Copy data files from board to local backup

fs.mv("/app/main.py", "/")              # Move main.py from app dir on board to /main.py
fs.mkdir("/app/backup")                 # Create a backup dir on the board
fs.cp("/app/*.py", "/app/backup")       # Copy the .py files to backup dir on board

fs.touch("/timestamp.dat")              # Create or update timestamp file
fs.rm("/lib/*.py")                      # Delete all .py files in /lib
fs.rm("/app", recursive=True)           # Delete the app directory and subdirs

fs.ls(remote, recursive=True)           # Print a listing of files in the app dir
fs.ls("/", long=True, recursive=True)   # Print a long-form listing
```

### Function Arguments

Many of these functions take a list of files, `FileList`, as one of their
arguments, eg. `fs.ls(), fs.put(), fs.get(), fs.cp(), fs.ls()`. A `FileList` can
be any one of:

- `Iterable[MPRemotePath | Path]`: eg. a list of file path instances,
- `Iterable[str]`: eg. a list of filenames (or wildcard patterns),
- `MPRemotePath | Path`: A single instance of a local or remote file path, or
- `str`: a whitespace separated list of filenames (or wildcard patterns)

If the function expects **local** file paths, string filenames will be
converted to `Path` instances, eg. the first argument of `put(files, dest)`.

If the function expects **remote** file paths, string filenames will be
converted to `MPRemotePath` instances, eg. the first arguments of
`get(files, dest)`, `ls(files)`, `cp(files, dest)`and `mv(files, dest)`.

### `mpremote_path.util.mpfs` Functions

**WARNING: This API is a work-in-progress and subject to wholsesale change.**

- **`connect(port: str) -> None`**

  - Establish a connection to the serial-attached micropython board. `port` is
    the name of a serial port (full or abbreviated), eg: `"/dev/ttyUSB0"` or
    `"u0"`, This function must be called before any methods that attempt to
    interact with the micropython board.

- **`mkdir(name: str) -> MPRemotePath`**

  - Create and return a directory on the micropython board.

- **`rmdir(name: str) -> None`**

  - Delete a directory on the micropython board (directory must be empty).

- **`cd(name: str) -> MPRemotePath`**

  - Set the working directory on the board to `name` and return the fully
    resolved path.

- **`cwd(name: str) -> MPRemotePath`**

  - Return the current working directory on the board.

- **`touch(name: str) -> MPRemotePath`**

  - Create a regular file on the micropython board. If the file exists, update
    the timestamp on the file.

- **`cat(files: FileList) -> None`**

  - Print out the contents of the files provided.

- **`rm(files: FileList, recursive: bool = False) -> None`**

  - Delete files and directories. Will delete contents of directories if
    `recursive` is set `True`.

- **`put(files: FileList, dest: MPRemotePath | str) -> MPRemotePath`**

  - Recursively copy all the local files and directories specified in `files`
    into the remote `dest` directory on the micropython board. The files
    specified in `files` and `dest` may be `Path` instances or `str` values
    (including glob patterns). Filenames provided as strings will be converted
    to local `Path` instances.

    Returns the destination directory as a `MPRemotePath` instance.

- **`get(files: FileList, dest: Path | str) -> Path`**

  - Recursively copy all the remote files and directories specified in `files`
    into the local `dest` directory. The files specified in `files` and `dest`
    may be `MPRemotePath` instances or `str` values (including glob patterns).
    Filenames provided as strings will be converted to local `MPRemotePath`
    instances.

    Returns the destination directory as a `Path` instance.

- **`mv(files: FileList, dest: MPRemotePath | str) -> MPRemotePath`**

  - Move files and directories on the board (specified in `files`) into the
    `dest` directory on the board. The files specified in `FileList` and `dest`
    may be `MPRemotePath` instances or `str` values (including glob patterns).
    Filenames provided as strings will be converted to `MPRemotePath` instances.

    Returns the destination directory as a `MPRemotePath` instance.

- **`cp(files: FileList, dest: MPRemotePath | str) -> MPRemotePath`**

  - Recursively copy files and directories on the board (specified in `files`)
    into the `dest` directory on the board. The files specified in `files`
    and `dest` may be `MPRemotePath` instances or `str` values (including glob
    patterns). Filenames provided as strings will be converted to `MPRemotePath`
    instances.

    Returns the destination directory as a `MPRemotePath` instance.

## `mpremote_path.util.mpfsops` module

**WARNING: This API is a work-in-progress and subject to wholsesale change.**

### `mpfsops` Features

Provides utility functions for working with files on a serial-attached
micropython board. These provide the underlying functionality used by the `mpfs`
module.

These functions accept `pathlib.Path` instances as arguments (including
`MPRemotePath` instances). They work transparently with local files and files on
a micropython board. *Be careful that you know which files you are working
with!!!*

```py
from pathlib import Path
from mpremote_path import MPath
from mpremote_path.util import mpfsops as fsops

fsops.connect("u0")                 # Use device attached to /dev/ttyUSB0

# Make a local copy of a local file (like `os.copyfile()`)
fsops.copyfile(Path("main.py"), Path("main-backup.py"))
# Copy a local file to the board
fsops.copyfile(Path("main.py"), MPath("/main.py"))
# Make a remote copy of a remote file on the board
fsops.copyfile(MPath("/main.py"), MPath("/main-backup.py"))
# Make a local copy of a remote file on the board
fsops.copyfile(MPath("/boot.py"), Path("boot.py"))

local = Path("app")                     # Directory on local host
remote = MPath("/app")                  # Directory on micropython board
remote.mkdir()

# Recursively copy app files to the board
fsops.copy([local / "data", local.glob("*.py")], remote)
# Recursively copy files from the board to a local directory
fsops.copy([remote / "data"], local)

# Move main.py from app dir on board to /main.py
fsops.move([remote / "main.py"], MPath("/"))

fsops.remove(remote.glob("*.py"))       # Delete all .py files in /app on board
fsops.remove([MPath("/app")], recursive=True) # Delete the app directory and subdirs
```

### `mpremote_path.util.mpfsops` Functions

**WARNING: This API is a work-in-progress and subject to wholsesale change.**

- **`connect(port: str) -> None`**

  - Establish a connection to the serial-attached micropython board. `port` is
    the name of a serial port (full or abbreviated), eg: `"/dev/ttyUSB0"` or
    `"u0"`, This function must be called before any methods that attempt to
    interact with the micropython board.

- **`copyfile(src: Path, dest: Path) -> Path | None`**

  - Create a new file `dest` which is a copy of the `src` file. `src` and `dest`
    may be `pathlib.Path` instances (representing a local file on the computer)
    OR `MPRemotePath` instances (representing files on the micropython board).
    `copyfile()` will use the most efficient way to copy the files to/from the
    board if required.

- **`copy(files: Iterable[Path], dest: Path) -> None`**

  - Recursively copy files and directories from `files` to `dest`. `files` is a
    list (or other iterable) of `Path` instances (which may also be
    `MPRemotePath` instances - representing files and direcories on the board).

    If `dest` is an existing directory (local or remote), all the files and dirs
    in the `files` list will be recursively copied into `dest`.

    If `dest` is **not** an existing directory **and** there is only one file or
    dir in `files`, the file/dir in `files` will be copied to a new file/dir
    named `dest`. (This is similar to how the unix `cp` command operates.)

- **`move(files: Iterable[Path], dest: Path) -> None`**

  - Recursively move files and directories from `files` to `dest`. `files` is a
    list (or other iterable) of `Path` instances (which may also be
    `MPRemotePath` instances - representing files and direcories on the board).

    If `dest` is an existing directory (local or remote), all the files and dirs
    in the `files` list will be recursively moved into `dest`.

    If `dest` is **not** an existing directory **and** there is only one file or
    dir in `files`, that file/dir in `files` will be renamed to `dest`. (This is
    similar to how the unix `mv` command operates.)

- **`remove(files: Iterable[Path], recursive: bool = False) -> None`**

  - Recursively (optionally) delete files and directories provided in `files`.
    `files` is a list (or other iterable) of `Path` instances (which may also be
    `MPRemotePath` instances - representing files and direcories on the board).

    If `recursive` is `True`, recursively delete any files and subdirectories
    inside directories to be deleted. If `recursive` is `False`, raise an
    exception if attempting to remove a directory that is not empty.
