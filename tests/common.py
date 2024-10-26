import itertools
from pathlib import Path
from typing import Iterable


def ls_dir(path: Path) -> Iterable[Path]:
    """List all the files and dirs recursively."""
    if path.is_dir():
        return itertools.chain(
            (child.relative_to(path) for child in path.iterdir()),
            itertools.chain.from_iterable(
                ls_dir(child) for child in path.iterdir() if child.is_dir()
            ),
        )
    raise ValueError(f"{path} is not a directory")


def check_folders(src: Path, dest: Path) -> None:
    local = sorted(f for f in ls_dir(src) if f.is_file())
    remote = sorted(f for f in ls_dir(dest) if f.is_file())
    assert [f.as_posix() for f in local] == [f.as_posix() for f in remote]
    assert [f.stat().st_size for f in local] == [f.stat().st_size for f in remote]
    for s, d in zip(local, remote):
        print(s.as_posix())
        assert s.read_bytes() == d.read_bytes()
