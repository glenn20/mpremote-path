import logging.config
import os
from contextlib import suppress
from pathlib import Path
from typing import Generator

import pytest
import yaml
from mpremote.transport_serial import TransportError
from mpremote_path import MPRemotePath as MPath

test_dir = "/_tests"  # Directory to create for tests on the micropython board.
data_dir = "tests/_data"  # Local directory containing test data files.


logging.config.dictConfig(yaml.safe_load(Path("tests/logging.yaml").read_text()))


def pytest_addoption(parser):
    parser.addoption(
        "--port",
        dest="port",
        action="store",
        default="/dev/ttyUSB0",
        help="Serial port for micropython board: /dev/ttyUSB0",
    )
    parser.addoption(
        "--baud",
        dest="baud",
        type=int,
        action="store",
        default=115200,
        help="Baud rate for serial port: 115200",
    )
    parser.addoption(
        "--sync",
        action="store_true",
        help="Whether to synchronise board clock with host: False",
    )
    parser.addoption(
        "--utc",
        action="store_true",
        help="Whether to use UTC for board clock: False",
    )


def rm_recursive(path: Path) -> None:
    """Remove a directory and all it's contents recursively."""
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


@pytest.fixture()
def root(pytestconfig) -> Generator[MPath, None, None]:
    if not hasattr(MPath, "board"):
        MPath.connect(
            pytestconfig.option.port,
            baud=pytestconfig.option.baud,
            set_clock=pytestconfig.option.sync,
            utc=pytestconfig.option.utc,
        )
        # MPath.board.soft_reset()
        rm_recursive(MPath(test_dir))  # Clean up after previous test runs
    path, pwd = MPath("/"), MPath.cwd()
    path.chdir()
    yield path
    pwd.chdir()


@pytest.fixture()
def testdir(root: MPath):
    path, pwd = MPath(test_dir), MPath.cwd()
    yield path
    if pwd:  # Restore the previous working directory and cleanup
        pwd.chdir()


@pytest.fixture()
def testfolder(root: MPath) -> Generator[MPath, None, None]:
    "Create a test folder on the board and cd into it."
    path, pwd = MPath(test_dir), MPath.cwd()
    if path in (pwd, *pwd.parents):
        MPath("/").chdir()
    rm_recursive(path)
    with suppress(TransportError, OSError):
        path.mkdir()
    path.chdir()
    try:
        yield path
    finally:
        pwd.chdir()
    with suppress(TransportError, OSError):
        rm_recursive(path)


@pytest.fixture()
def localdata() -> Generator[Path, None, None]:
    "Change to the local data directory."
    pwd = os.getcwd()
    os.chdir(data_dir)
    rm_recursive(Path("test2"))
    try:
        yield Path(".").resolve()
    finally:
        # rm_recursive(Path("test2"))
        os.chdir(pwd)
    with suppress(TransportError, OSError):
        rm_recursive(Path("test2"))
