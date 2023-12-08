import stat

import pytest
from mpremote_path import RemotePath


def test_root_folder(root):
    """Test the RemotePath class."""
    p = RemotePath("/")
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
    assert RemotePath("~").expanduser().as_posix() == "/"
    assert RemotePath("~/boot.py").expanduser().as_posix() == "/boot.py"


def test_mkdir(testdir: RemotePath) -> None:
    "Test creating and deleting directories"
    p = testdir
    assert p.exists() is False
    p.mkdir()
    assert p.exists() is True
    assert stat.S_ISDIR(p.stat().st_mode) is True
    assert (p.is_dir(), p.is_file()) == (True, False)
    p.rmdir()
    assert p.exists() is False


def test_cd(testdir: RemotePath) -> None:
    "Test changing directories"
    p = testdir
    assert p.exists() is False
    p.mkdir()
    assert p.exists() is True
    p.cd()
    assert p.cwd().as_posix() == testdir.as_posix()
    RemotePath("/").cd()
    assert p.cwd().as_posix() == "/"
    p.rmdir()
    assert p.exists() is False


def test_touch_unlink(testfolder: RemotePath) -> None:
    "Test creating and deleting files"
    p = RemotePath("test1.touch")
    assert p.exists() is False
    p.touch()
    assert p.exists() is True
    assert stat.S_ISREG(p.stat().st_mode) is True
    assert (p.exists(), p.is_dir(), p.is_file()) == (True, False, True)
    assert p.stat().st_size == 0
    p.unlink()
    assert p.exists() is False


def test_read_write_bytes(testfolder: RemotePath) -> None:
    "Test reading and writing bytes to/from files"
    p = RemotePath("test1.bytes")
    assert p.exists() is False
    msg = b"Hello world\n"
    p.write_bytes(msg)
    assert (p.exists(), p.is_dir(), p.is_file()) == (True, False, True)
    assert p.stat().st_size == len(msg)
    msg2 = p.read_bytes()
    assert msg2 == msg
    p.unlink()
    assert p.exists() is False


def test_read_write_text(testfolder: RemotePath) -> None:
    "Test reading and writing unicode strings to/from files"
    p = RemotePath("test1.text")
    assert p.exists() is False
    msg = "Hello world\n"
    p.write_text(msg)
    assert p.stat().st_size == len(msg)
    msg2 = p.read_text()
    assert msg2 == msg
    p.unlink()
    assert p.exists() is False


def test_resolve(root) -> None:
    "Test resolving paths: absolute(), and resolve()"
    q = RemotePath("./lib/mpy")
    q = q / "../.././main.py"
    assert (
        q.as_posix(),
        q.absolute().as_posix(),
        q.absolute().resolve().as_posix(),
    ) == (
        "lib/mpy/../../main.py",
        "/lib/mpy/../../main.py",
        "/main.py",
    )


def test_not_implemented(testfolder: RemotePath) -> None:
    "Test methods that are not implemented."
    p = RemotePath("test1.touch")
    assert p.exists() is False
    p.touch()
    assert p.exists() is True
    with pytest.raises(NotImplementedError):
        p.samefile("test1.touch")
    with pytest.raises(NotImplementedError):
        p.readlink()
    with pytest.raises(NotImplementedError):
        p.chmod(0o777)
    with pytest.raises(NotImplementedError):
        p.lchmod(0o777)
    with pytest.raises(NotImplementedError):
        p.replace("test2.touch")
    with pytest.raises(NotImplementedError):
        p.symlink_to("test2.touch")
    with pytest.raises(NotImplementedError):
        p.hardlink_to("test2.touch")
    with pytest.raises(NotImplementedError):
        p.link_to("test2.touch")
