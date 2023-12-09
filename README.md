# mpremote-path

Provides a [`pathlib`](https://docs.python.org/3/library/pathlib.html)
compatible interface to access and manipulate files on a serial-attached
[micropython](https://github.com/micropython/micropython) board from the host
computer. **mpremote-path** is built on the file access features of the
[mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html) tool.

**Contents: [Features](#features) | [Installation](#installation)**

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
print(f for f in MPath("/lib").rglob("*.py"))  # Print all python files in subdirs of /lib
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
            rsync(child, dst / child.name)
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

- Install in "editable mode":

  ```bash
  pip install -e .
  ```

- OR build and install a distributable `.whl` package

  ```bash
  python -m build
  pip install dist/mpremote-path*.whl
  ```

Run the test suite (requires `pytest`):

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
