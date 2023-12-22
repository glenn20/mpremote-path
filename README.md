# mpremote-path

Provides a [`pathlib`](https://docs.python.org/3/library/pathlib.html)
compatible interface to access and manipulate files on a serial-attached
[micropython](https://github.com/micropython/micropython) board from the host
computer. **mpremote-path** is built on the file access features of the
[mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html) tool.

**Contents: [Features](#features) | [Installation](#installation) | [API Docs](#api-docs-mpremote_path-module)**

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

- inherits from `PosixPath` class, so code which works on `Path` objects will
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

# Make a local copy of a directory
rcopy(Path("./app"), Path("../app-backup"))

# Copy local directory to the micropython board
rcopy(Path("./app"), MPath("/lib/app"))

# Copy a directory from the micropython board to the local disk
rcopy(MPath("/lib"), Path("./lib"))
```

## Installation

First, clone this github repo into a folder somewhere:

```bash
git clone https://github.com/glenn20/mpremote-path
cd mpremote-path
```

If you use a python virtual environment (recommended), make sure it is active.

To install in your python environment:

- Install in ["editable
  mode"](https://setuptools.pypa.io/en/latest/userguide/development_mode.html):

  ```bash
  pip install -e .
  ```

- OR build and install a distributable `.whl` package

  ```bash
  python -m build
  pip install dist/mpremote-path*.whl
  ```

*Optional*: Run the test suite (requires pytest module: `pip install pytest`):

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

#### Additional methods (nor present in ordinary `Path` instances)

- Classmethod: **`connect(port: str | Board | SerialTransport) -> None`**

  - Establish a connection to the serial-attached micropython board. `port` may
    be of type:
    - `str`: the name of a serial port (full or abbreviated), eg:
      `"/dev/ttyUSB0"` or `"u0"`,
    - `SerialTransport`: the mpremote interface to the micropython board, or
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
    instance.

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
      - eg. `lib = MPRemotePath("/lib); pkg_dir = lib / "pkg"`.

- Inherits or overrides from
  [pathlib.Path](https://docs.python.org/3/library/pathlib.html#pathlib.Path):

  - *Methods*:
    - `cwd()`, `home()`, `stat()`, `exists()`, `expanduser()`, `glob(pattern)`,
      `group()`, `is_dir()`, `is_file()`, `is_junction()`, `is_mount()`,
      `samefile(other)`, `is_symlink()`, `is_socket()`, `is_fifo()`,
      `is_block_device()`, `is_char_device()`, `iterdir()`, `walk()`, `lstat()`,
      `mkdir()`, `owner()`, `read_bytes()`, `read_text()`, `rename(target)`,
      `replace(target)`, `absolute()`, `resolve()`, `rglob(pattern)`, `rmdir()`,
      `touch()`, `unlink()`, `write_bytes(data)`, `write_text(text)`
  - *Will raise a `NotImplemented` exception*:
    - `chmod()`, `lchmod()`, `open()`, `read_link()`, `symlimk_to(target)`,
      `hardlink_to(target)`

## `mpremote_path.utils` module


