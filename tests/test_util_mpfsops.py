from pathlib import Path

from common import check_folders

from mpremote_path import MPRemotePath as MPath
from mpremote_path.util import mpfsops

# The `root` fixture saves the current working directory, cd's to the root
# folder and passes in the path of the root directory of the micropython board.
# The original working directory will be restored when the fixture is torn down.

# The `testdir` fixture passes in a directory for testing without creating the
# directory.

# The `testfolder` fixture creates a directory on the board for running tests
# and passes in the path of the directory. The folder will be deleted when the
# test fixture is torn down.


def copyfile_check(src: Path, dest: Path) -> None:
    assert (src.exists(), dest.exists()) == (True, False)
    mpfsops.copyfile(src, dest)
    assert (src.exists(), dest.exists()) == (True, True)
    assert dest.stat().st_size == src.stat().st_size
    assert dest.read_bytes() == src.read_bytes()


def test_copyfile(testfolder: MPath, localdata: Path) -> None:
    "Test copying files to and from the board."
    src, dest = Path("./src/ota/status.py"), MPath("status.py")
    copyfile_check(src, dest)  # Copy local to the board
    dest2 = MPath("status2.py")
    copyfile_check(dest, dest2)  # Make a second copy on the board
    dest3 = Path("status3.py")
    copyfile_check(dest2, dest3)  # Copy from the board to a local file
    dest4 = Path("status4.py")
    copyfile_check(dest3, dest4)  # Make a second local copy
    for f in (dest, dest2, dest3, dest4):
        f.unlink()  # Clean up


def test_copypath(testfolder: MPath, localdata: Path) -> None:
    "Test recursively copying a local file/dir to the micropython board."
    src, dest = Path("./src"), MPath("./src")
    assert (src.exists(), dest.exists()) == (True, False)
    mpfsops.copypath(src, dest)
    assert (dest.exists(), dest.is_dir(), dest.is_file()) == (True, True, False)


def test_rcopy(testfolder: MPath, localdata: Path) -> None:
    "Test recursively copying local files/dirs to the micropython board."
    src, dest = Path("./src"), MPath("./src2")
    assert (src.exists(), dest.exists()) == (True, False)
    mpfsops.rcopy(src, dest)
    assert (dest.exists(), dest.is_dir(), dest.is_file()) == (True, True, False)


def test_copy_file(testfolder: MPath, localdata: Path) -> None:
    "Test copying a local file to the micropython board."
    src, dest = Path("./src/ota/status.py"), MPath("status.py")
    assert (src.exists(), dest.exists()) == (True, False)
    mpfsops.copy([src], dest)
    assert (dest.exists(), dest.is_dir(), dest.is_file()) == (True, False, True)


def test_copy_folder(testfolder: MPath, localdata: Path) -> None:
    "Test recursively copying local files to the micropython board."
    src, dest = Path("./src"), MPath(".")
    assert (src.exists(), dest.exists()) == (True, True)
    mpfsops.copy([src], dest)
    check_folders(src, dest / src.name)


def test_remove_file(testfolder: MPath, localdata: Path) -> None:
    "Test deleting files on board."
    src, dest = Path("./src/ota/status.py"), MPath("status.py")
    assert (src.exists(), dest.exists()) == (True, False)
    mpfsops.copy([src], dest)
    assert (dest.exists(), dest.is_dir(), dest.is_file()) == (True, False, True)
    mpfsops.remove([dest])
    assert (dest.exists(), dest.is_dir(), dest.is_file()) == (False, False, False)


def test_remove_folder(testfolder: MPath, localdata: Path) -> None:
    "Test deleting folders on board."
    src, dest = Path("./src"), MPath("./src2")
    assert (src.exists(), dest.exists()) == (True, False)
    mpfsops.rcopy(src, dest)
    assert (dest.exists(), dest.is_dir(), dest.is_file()) == (True, True, False)
    mpfsops.remove([dest], recursive=True)
    assert (dest.exists(), dest.is_dir(), dest.is_file()) == (False, False, False)


def test_move_file(testfolder: MPath, localdata: Path) -> None:
    "Test renaming files on the board."
    src, dest = Path("./src/ota/status.py"), MPath("status.py")
    assert (src.exists(), dest.exists()) == (True, False)
    mpfsops.copy([src], dest)
    assert (dest.exists(), dest.is_dir(), dest.is_file()) == (True, False, True)
    dest2 = MPath("status2.py")
    mpfsops.move([dest], dest2)
    assert (dest.exists(), dest.is_dir(), dest.is_file()) == (False, False, False)
    assert (dest2.exists(), dest2.is_dir(), dest2.is_file()) == (True, False, True)


def test_move_folder(testfolder: MPath, localdata: Path) -> None:
    "Test renaming folders on the board."
    src, dest = Path("./src"), MPath("src")
    assert (src.exists(), dest.exists()) == (True, False)
    mpfsops.rcopy(src, dest)
    assert (dest.exists(), dest.is_dir(), dest.is_file()) == (True, True, False)
    dest2 = MPath("src2")
    mpfsops.move([dest], dest2)
    assert (dest.exists(), dest.is_dir(), dest.is_file()) == (False, False, False)
    assert (dest2.exists(), dest2.is_dir(), dest2.is_file()) == (True, True, False)
