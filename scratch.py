# %%
# pyright: reportUnusedExpression=false
import itertools
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Iterable

from mpremote.transport_serial import SerialTransport

from mpremote_path import Board, Debug
from mpremote_path import MPRemotePath as MPath

MPath.board = Board(SerialTransport("/dev/ttyUSB0"))
board = MPath.board
board.debug = Debug.EXEC
board.soft_reset()
p = MPath("main.py", board=board)
d = MPath("/", board=board)
dot = MPath(".")

print(repr(p))
(d.stat(), d.is_dir(), d.is_file())

# %%
p.cwd(), p.home()

# %%
print(list(d.iterdir()))
print(list(dot.iterdir()))

# %%
list(dot.glob("*.py"))

# %%
list(dot.rglob("*.py"))

# %%
p.read_bytes()
print(p.read_text())

# %%
p2 = MPath("crap.txt")
msg = b"Hello world\n"
p2.write_bytes(msg)
p2.stat()
msg2 = p2.read_bytes()
print(msg2)
assert msg2 == msg
p2.unlink()
"OK"

# %%
q = MPath("./lib/mpy")
q = q / "../.././main.py"
q, q.absolute(), q.absolute().resolve()

# %%
missing = MPath("missing.txt")
assert missing.exists() is False
missing.exists()


# %%
@contextmanager
def folder(name: str) -> Generator[MPath, None, None]:
    pwd, d = None, None
    try:
        pwd = MPath.cwd()
        d = MPath(name)
        d.mkdir()
        d.chdir()
        yield d
    finally:
        if pwd:
            pwd.chdir()
        if d:
            d.rmdir()


def copy_recursive(src: Path, dst: Path) -> None:
    """Copy a file or directory recursively."""
    if src.is_dir():
        print(f"{src}/ -> {dst}/")
        dst.mkdir()
        for child in src.iterdir():
            copy_recursive(child, dst / child.name)
    elif src.is_file():
        print(f"{src} -> {dst}")
        dst.write_bytes(src.read_bytes())
    else:
        print(f"Skipping {src}")


def ls_dir(path: Path) -> Iterable[Path]:
    """List a file or directory recursively."""
    if path.is_dir():
        return itertools.chain(
            (child for child in path.iterdir()),
            itertools.chain.from_iterable(
                ls_dir(child) for child in path.iterdir() if child.is_dir()
            ),
        )
    raise ValueError(f"{path} is not a directory")


def rm_recursive(path: Path) -> None:
    if not path.exists():
        return
    elif path.is_dir():
        for child in path.iterdir():
            rm_recursive(child)
        print(f"{path}")
        path.rmdir()
    elif path.is_file():
        print(f"{path}")
        path.unlink()
    else:
        raise ValueError(f"{path} is not a directory or file")


# %%
p = MPath("/_test")
if not p.exists():
    p.mkdir()
p.chdir()
if Path.cwd().name != "_test_data":
    os.chdir("_test_data")


# %%
src = Path("./lib")
dest = MPath("./lib")
copy_recursive(src, dest)
local = sorted([f for f in ls_dir(src) if f.is_file()])
files = sorted([f for f in ls_dir(dest) if f.is_file()])

# %%
ls_local = sorted([f.as_posix() for f in local])
ls_dest = sorted([f.as_posix() for f in files])
print(ls_local, ls_dest)
assert ls_local == ls_dest
print([f.stat().st_size for f in local], [f.stat().st_size for f in files])
assert [f.stat().st_size for f in local] == [f.stat().st_size for f in files]
for src, dst in zip(local, files):
    print(src.as_posix())
    assert src.read_bytes() == dst.read_bytes()

# %%
p.parent.chdir()
rm_recursive(p)
assert p.exists() is False

# %%
p = MPath("/_test").resolve()
q = Path("_test_data")
list(p.rglob("*.py"))

# %%
