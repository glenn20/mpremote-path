import argparse
import logging.config
import os
from contextlib import suppress
from pathlib import Path
from typing import Generator

import pytest
import unix_port
import yaml
from mpremote.transport_serial import TransportError

from mpremote_path import MPRemotePath as MPath

# Set the default serial port for the micropython board to use the unix port.
default_port = "unix"
default_baud_rate = 2000000

tests_dir = Path(__file__).parent  # Base directory for the tests.
data_dir = tests_dir / "_data"  # Local directory containing test data files.
logging_config = tests_dir / "logging.yaml"  # Logging configuration file.

board_test_dir = "/_tests"  # Directory to create for tests on the micropython board.

logging.config.dictConfig(yaml.safe_load(logging_config.read_text()))


def pytest_addoption(parser: argparse.Namespace) -> None:
    parser.addoption(
        "--port",
        dest="port",
        action="store",
        default=default_port,
        help="Serial port for micropython board: /dev/ttyUSB0",
    )
    parser.addoption(
        "--baud",
        dest="baud",
        type=int,
        action="store",
        default=default_baud_rate,
        help=f"Baud rate for serial port: {default_baud_rate}",
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
    if path.is_file():
        path.unlink()
    elif path.is_dir():
        for child in path.iterdir():
            rm_recursive(child)
        path.rmdir()
    elif path.exists():
        raise ValueError(f"{path} is not a directory or file")
    else:
        pass


@pytest.fixture(scope="session")
def serial_port(
    tmp_path_factory: pytest.TempPathFactory,
    pytestconfig: argparse.Namespace,
) -> Generator[str, None, None]:
    """Create a serial port for the micropython board.
    If the port is set to `unix`, run the unix port using socat."""
    port = pytestconfig.option.port
    if port == "unix":
        with unix_port.run_micropython(
            tmp_path_factory.mktemp("unix_micropython")
        ) as port:
            yield port  # Return the path to the PTY as the serial port
    else:
        yield port  # Return the serial port name as is


@pytest.fixture(scope="session")
def root(
    serial_port: str,
    pytestconfig: argparse.Namespace,
) -> Generator[MPath, None, None]:
    "Connect to the micropython board and change to the root directory."
    MPath.connect(
        serial_port,
        baud=pytestconfig.option.baud,
        set_clock=pytestconfig.option.sync,
        utc=pytestconfig.option.utc,
    )
    rm_recursive(MPath(board_test_dir))  # Clean up after previous test runs
    path, pwd = MPath("/"), MPath.cwd()
    path.chdir()
    yield path
    pwd.chdir()


@pytest.fixture()
def testdir(root: MPath) -> Generator[MPath, None, None]:
    path, pwd = MPath(board_test_dir), MPath.cwd()
    yield path
    if pwd:  # Restore the previous working directory and cleanup
        pwd.chdir()


@pytest.fixture()
def testfolder(root: MPath) -> Generator[MPath, None, None]:
    "Create a test folder on the board and cd into it."
    path, pwd = MPath(board_test_dir), MPath.cwd()
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
        yield Path.cwd()
    finally:
        rm_recursive(Path("test2"))
        os.chdir(pwd)
