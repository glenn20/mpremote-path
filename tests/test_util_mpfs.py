from pathlib import Path

from common import check_folders

from mpremote_path import MPRemotePath as MPath
from mpremote_path.util import mpfs as fscmd

# The `root` fixture saves the current working directory, cd's to the root
# folder and passes in the path of the root directory of the micropython board.
# The original working directory will be restored when the fixture is torn down.

# The `testfolder` fixture creates a directory on the board for running tests
# and passes in the path of the directory. The folder will be deleted when the
# test fixture is torn down.


def test_touch(testfolder: MPath) -> None:
    "Test creating a file"
    name = "test1.file"
    p = fscmd.touch(name)
    assert p.is_file() is True
    assert MPath(name).is_file() is True


def test_rmfile(testfolder: MPath) -> None:
    "Test deleting a file"
    name = "test1.file"
    p = fscmd.touch(name)
    assert p.is_file() is True
    fscmd.rm(name)
    assert MPath(name).exists() is False


def test_mkdir(testfolder: MPath) -> None:
    "Test creating a directory"
    name = "test1.folder"
    p = fscmd.mkdir(name)
    assert p.is_dir() is True
    assert MPath(name).is_dir() is True


def test_rmdir(testfolder: MPath) -> None:
    "Test deleting a directory"
    name = "test1.folder"
    p = fscmd.mkdir(name)
    assert p.is_dir() is True
    fscmd.rmdir(name)
    q = MPath(name)
    assert q.exists() is False


def test_cd_cwd(testfolder: MPath) -> None:
    "Test changing directories"
    name = "testcd.folder"
    p = fscmd.mkdir(name)
    assert p.is_dir() is True
    p2 = fscmd.cd(name)
    assert (
        fscmd.cwd().as_posix()
        == (testfolder / name).as_posix()
        == p2.resolve().as_posix()
    )


def test_cp_file(testfolder: MPath) -> None:
    "Test make a copy of a file onm the board."
    src, dst = "test1.file", "test2.file"
    p = MPath(src)
    assert p.exists() is False
    msg = "Hello world\n"
    p.write_text(msg)
    assert p.is_file() is True
    fscmd.cp(src, dst)
    q = MPath(dst)
    assert q.exists() is True
    assert q.read_text() == msg


def test_put_file(testfolder: MPath, localdata: Path) -> None:
    "Test copy file to board"
    src, dst = "./src/ota/status.py", "./status2.py"
    fscmd.put(src, dst)
    assert MPath(dst).read_text() == Path(src).read_text()


def test_put_dir(testfolder: MPath, localdata: Path) -> None:
    "Test copy directory and contents to board."
    src, dst = "src", "."
    fscmd.put(src, dst)
    p = Path(src)
    check_folders(p, MPath(dst) / p.name)


def test_put_glob(testfolder: MPath, localdata: Path) -> None:
    "Test copy file by globbing to board"
    src, dst = "./src/ota/*.py", "."
    fscmd.put(src, dst)
    q = MPath(dst)
    for p in Path("./src/ota").glob("*.py"):
        assert p.read_text() == (q / p.name).read_text()


def test_get_file(testfolder: MPath, localdata: Path) -> None:
    "Test copy file from board"
    src, dst = "test1", "test2"
    msg = "Hello world\n"
    MPath(src).write_text(msg)
    fscmd.get(src, dst)
    assert Path(dst).read_text() == MPath(src).read_text()


def test_get_dir(testfolder: MPath, localdata: Path) -> None:
    "Test copy directory and contents from board"
    src, dst, dst2 = "src", ".", "test2"
    fscmd.put(src, dst)
    q = Path(dst2)
    q.mkdir()
    fscmd.get(src, dst2)
    check_folders(MPath(src), q / src)


def test_get_glob(testfolder: MPath, localdata: Path) -> None:
    "Test copy file globs from board"
    src, dst, dst2 = "src", ".", "test2"
    fscmd.put(src, dst)
    q = Path(dst2)
    q.mkdir()
    fscmd.get("src/ota/*.py", dst2)
    for p in Path("./src/ota").glob("*.py"):
        assert p.read_text() == (q / p.name).read_text()
