import argparse
import logging.config
import os
import platform
import shutil
import subprocess
import time
from contextlib import suppress
from pathlib import Path
from typing import Generator

import pytest
import yaml
from mpremote.transport_serial import TransportError

from mpremote_path import MPRemotePath as MPath

board_test_dir = "/_tests"  # Directory to create for tests on the micropython board.

tests_dir = Path(__file__).parent  # Base directory for the tests.
data_dir = tests_dir / "_data"  # Local directory containing test data files.
logging_config = tests_dir / "logging.yaml"  # Logging configuration file.

# Where to find the micropython unix port and the initialisation script.
unix_dir = tests_dir / "unix-micropython"
unix_micropython = unix_dir / "micropython -i -m boot"
unix_micropython_boot = unix_dir / "boot.py"  # Initialisation script.

# Set the default serial port for the micropython board to use the unix port.
default_port = "unix"

logging.config.dictConfig(yaml.safe_load(logging_config.read_text()))

# Install the socat package if running as a Github Action.
if os.getenv("GITHUB_ACTIONS"):
    osname = platform.system()
    if osname == "Linux":
        subprocess.run("sudo apt-get install socat".split(), check=True)
    else:
        raise RuntimeError(f"Micropython unix port not supported on {osname}.")


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
        default=921600,
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
    If the port is set to `unix`, create a unix port using socat."""
    port = pytestconfig.option.port
    if port != "unix":
        yield port
        return
    wd = tmp_path_factory.mktemp("unix_micropython")
    unix_pty = wd / "pty"
    unix_fs = wd / "fs"
    unix_fs.mkdir()
    # Copy the boot.py script to the filesystem directory
    # This is used to initialise the RAM filesystem on the unix port.
    shutil.copy(unix_micropython_boot, unix_fs)
    proc = subprocess.Popen(
        [
            "socat",
            f"PTY,link={unix_pty},rawer,b4000000",
            f"EXEC:{unix_micropython},pty,stderr,onlcr=0,b4000000",
        ],
        cwd=unix_fs,
    )
    time.sleep(0.1)
    yield str(unix_pty)
    proc.terminate()


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
