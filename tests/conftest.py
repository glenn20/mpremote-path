import os
from contextlib import suppress
from pathlib import Path
from typing import Generator

import pytest
from mpremote.transport_serial import SerialTransport, TransportError
from mpremote_path import Board, RemotePath

test_dir = "/_tests"
data_dir = "tests/_data"


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


@pytest.fixture()
def root(pytestconfig) -> Generator[RemotePath, None, None]:
    if not hasattr(RemotePath, "board"):
        RemotePath.board = Board(
            SerialTransport(pytestconfig.option.port, pytestconfig.option.baud)
        )
        RemotePath.board.soft_reset()
        rm_recursive(RemotePath(test_dir))  # Clean up after previous test runs
    path, pwd = RemotePath("/"), RemotePath.cwd()
    path.cd()
    yield path
    pwd.cd()


@pytest.fixture()
def testdir(root):
    return RemotePath(test_dir)


@pytest.fixture()
def testfolder(root: RemotePath) -> Generator[RemotePath, None, None]:
    "Create a test folder on the board and cd into it."
    path = RemotePath(test_dir)
    pwd = RemotePath.cwd()
    with suppress(TransportError, OSError):
        path.mkdir()
    path.cd()
    yield path
    if pwd:  # Restore the previous working directory and cleanup
        pwd.cd()
    with suppress(TransportError, OSError):
        path.rmdir()


@pytest.fixture()
def localdata() -> Generator[Path, None, None]:
    "Change to the local data directory."
    pwd = os.getcwd()
    os.chdir(data_dir)
    yield Path(".").resolve()
    os.chdir(pwd)
