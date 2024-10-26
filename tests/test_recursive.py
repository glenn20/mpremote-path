import itertools
from pathlib import Path
from typing import Iterable

from mpremote_path import MPRemotePath as MPath


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
    """List all the files and dirs recursively."""
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
        path.rmdir()
    elif path.is_file():
        path.unlink()
    else:
        raise ValueError(f"{path} is not a directory or file")


def test_recursive_copy(testfolder: MPath, localdata: Path) -> None:
    "Test recursively copying local files to the micropython board."
    src, dest = Path("./src"), MPath("./src")
    assert (src.exists(), dest.exists()) == (True, False)
    copy_recursive(src, dest)
    local = sorted([f for f in ls_dir(src) if f.is_file()])
    files = sorted([f for f in ls_dir(dest) if f.is_file()])
    assert [f.as_posix() for f in local] == [f.as_posix() for f in files]
    assert [f.stat().st_size for f in local] == [f.stat().st_size for f in files]
    for s, d in zip(local, files):
        print(s.as_posix())
        assert s.read_bytes() == d.read_bytes()


def test_glob_rglob(testfolder: MPath, localdata: Path) -> None:
    "Test glob methods."
    src, dest = Path("./src"), MPath("./src")
    assert (src.exists(), dest.exists()) == (True, False)
    copy_recursive(src, dest)
    assert sorted([f.as_posix() for f in (src / "ota").glob("*.py")]) == sorted(
        [f.as_posix() for f in (dest / "ota").glob("*.py")]
    )
    assert sorted([f.as_posix() for f in src.rglob("*.py")]) == sorted(
        [f.as_posix() for f in dest.rglob("*.py")]
    )


def test_recursive_rm(testfolder: MPath, localdata: Path) -> None:
    "Test recursively deleting files and directories."
    _src, dest = Path("./src"), MPath("./src")
    rm_recursive(dest)
    assert dest.exists() is False
