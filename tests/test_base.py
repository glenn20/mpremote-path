import stat
from shutil import SameFileError

import pytest

from mpremote_path import MPRemotePath as MPath

# The `root` fixture saves the current working directory, cd's to the root
# folder and passes in the path of the root directory of the micropython board.
# The original working directory will be restored when the fixture is torn down.

# The `testdir` fixture passes in a directory for testing without creating the
# directory.

# The `testfolder` fixture creates a directory on the board for running tests
# and passes in the path of the directory. The folder will be deleted when the
# test fixture is torn down.


def test_root_folder(root: MPath) -> None:
    """Test the RemotePath class."""
    p = MPath("/")
    assert p.exists() is True
    assert len(list(p.stat())) == 10
    assert stat.S_ISDIR(p.stat().st_mode) is True
    assert p.is_dir() is True
    assert p.is_file() is False
    assert p.is_mount() is False
    assert p.is_symlink() is False
    assert p.is_block_device() is False
    assert p.is_char_device() is False
    assert p.is_fifo() is False
    assert p.is_socket() is False
    assert p.cwd().as_posix() == "/"
    assert p.home().as_posix() == "/"
    assert MPath("~").expanduser().as_posix() == "/"
    assert MPath("~/boot.py").expanduser().as_posix() == "/boot.py"


def test_mkdir(testdir: MPath) -> None:
    "Test creating and deleting directories"
    p = testdir
    assert p.exists() is False
    p.mkdir()
    assert p.exists() is True
    assert stat.S_ISDIR(p.stat().st_mode) is True
    assert (p.is_dir(), p.is_file()) == (True, False)
    p.rmdir()
    assert p.exists() is False


def test_cd(testdir: MPath) -> None:
    "Test changing directories"
    p = testdir
    assert p.exists() is False
    p.mkdir()
    assert p.exists() is True
    p.chdir()
    assert p.cwd().as_posix() == testdir.as_posix()
    MPath("/").chdir()
    assert p.cwd().as_posix() == "/"
    p.rmdir()
    assert p.exists() is False


def test_touch_unlink(testfolder: MPath) -> None:
    "Test creating and deleting files"
    p = MPath("test1.touch")
    assert p.exists() is False
    p.touch()
    assert p.exists() is True
    assert stat.S_ISREG(p.stat().st_mode) is True
    assert (p.exists(), p.is_dir(), p.is_file()) == (True, False, True)
    assert p.stat().st_size == 0
    p.unlink()
    assert p.exists() is False


def test_rename_replace(testfolder: MPath) -> None:
    "Test renaming files"
    p = MPath("test1.touch")
    p.touch()
    assert p.exists() and p.is_file()
    q = p.rename("test2.touch")
    assert q.exists() and q.is_file()
    assert p.exists() is False
    p = q.replace("test3.touch")
    assert p.exists() and p.is_file()
    assert q.exists() is False
    p.unlink()
    assert p.exists() is False


def test_read_write_bytes(testfolder: MPath) -> None:
    "Test reading and writing bytes to/from files"
    p = MPath("test1.bytes")
    assert p.exists() is False
    msg = b"Hello world\n"
    p.write_bytes(msg)
    assert (p.exists(), p.is_dir(), p.is_file()) == (True, False, True)
    assert p.stat().st_size == len(msg)
    msg2 = p.read_bytes()
    assert msg2 == msg
    p.unlink()
    assert p.exists() is False


def test_read_write_text(testfolder: MPath) -> None:
    "Test reading and writing unicode strings to/from files"
    p = MPath("test1.text")
    assert p.exists() is False
    msg = "Hello world\n"
    p.write_text(msg)
    assert p.stat().st_size == len(msg)
    msg2 = p.read_text()
    assert msg2 == msg
    p.unlink()
    assert p.exists() is False


def test_resolve_samefile(root: MPath) -> None:
    "Test resolving paths: absolute(), and resolve()"
    q = MPath("./lib/mpy")
    q = q / "../.././main.py"
    assert q.as_posix() == "lib/mpy/../../main.py"
    assert q.absolute().as_posix() == "/lib/mpy/../../main.py"
    assert q.absolute().resolve().as_posix() == "/main.py"
    assert q.samefile(q.absolute()) is True
    assert q.samefile(q.absolute().resolve()) is True


def test_copy_copyfile(testfolder: MPath) -> None:
    "Test copying files"
    p = MPath("test1.touch")
    assert p.exists() is False
    msg = "Hello world\n"
    p.write_text(msg)
    assert p.is_file() is True
    q = p.copyfile("test2.touch")
    assert q.read_text() == msg
    q.unlink()
    d1 = testfolder / "dir1"
    d1.mkdir()
    q = p.copy(d1)
    assert str(q) == str(d1 / "test1.touch")
    assert q.read_text() == msg
    q.unlink()
    d1.rmdir()
    with pytest.raises(SameFileError):
        q = p.copy(testfolder)
    p.unlink()


def test_open_bytes(testfolder: MPath) -> None:
    "Test reading and writing bytes to/from files"
    p = MPath("test1.bytes")
    assert p.exists() is False
    msg = b"Hello world\n"
    f = p.open("wb")
    f.write(msg)
    f.close()
    assert (p.exists(), p.is_dir(), p.is_file()) == (True, False, True)
    assert p.stat().st_size == len(msg)
    msg2 = p.read_bytes()
    assert msg2 == msg
    f2 = p.open("rb")
    msg3 = f2.read()
    f2.close()
    assert msg3 == msg
    p.unlink()
    assert p.exists() is False


def test_open_text(testfolder: MPath) -> None:
    "Test reading and writing bytes to/from files"
    p = MPath("test1.text")
    assert p.exists() is False
    msg = "Hello world\n"
    f = p.open("w", newline="")  # Preserve unix newlines on Windows
    f.write(msg)
    f.close()
    assert (p.exists(), p.is_dir(), p.is_file()) == (True, False, True)
    msg2 = p.read_text()
    assert msg2 == msg
    f = p.open("r")
    msg3 = f.read()
    f.close()
    assert msg3 == msg
    p.unlink()
    assert p.exists() is False


def test_not_implemented(testfolder: MPath) -> None:
    "Test methods that are not implemented."
    p = MPath("test1.touch")
    assert p.exists() is False
    p.touch()  # Create a temp file for the following tests
    assert p.exists() is True
    with pytest.raises(NotImplementedError):
        p.chmod(0o777)  # No groups or other permissions on lfs or fat
    with pytest.raises(NotImplementedError):
        p.lchmod(0o777)  # No groups or other permissions on lfs or fat
    with pytest.raises(NotImplementedError):
        p.readlink()  # No links on lfs or fat
    with pytest.raises(NotImplementedError):
        p.symlink_to("test2.touch")  # No links on lfs or fat
    with pytest.raises(NotImplementedError):
        p.hardlink_to("test2.touch")  # No links on lfs or fat
    with pytest.raises(NotImplementedError):
        p.link_to("test2.touch")  # No links on lfs or fat
    p.unlink()
