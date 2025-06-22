import argparse
import logging.config
import os
from pathlib import Path
from typing import Generator

import pytest
import unix_port
import yaml

from mpremote_path import MPRemotePath as MPath

# Set the default serial port for the micropython board to use the unix port.
default_port = "unix"
default_baud_rate = 115200

# Location of the tests and data directories on the local filesystem.
tests_dir = Path(__file__).parent  # Base directory for the tests.
data_dir = tests_dir / "_data"  # Local directory containing test data files.
logging_config = tests_dir / "logging.yaml"  # Logging configuration file.

# Directory to create for tests on the micropython board.
board_test_dir = "_mpremote_path_tests"

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
    parser.addoption(
        "--use-socat",
        action="store_true",
        help="Whether to use socat for PTY emulation: False",
    )
    parser.addoption(
        "--debug-board",
        action="store_true",
        help="Whether to enable debug output: False",
    )


# TODO: Make this a function on the board.
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
    If the port is set to `unix`, run the unix port behind a PTY."""
    port = pytestconfig.option.port
    use_socat = pytestconfig.option.use_socat
    debug = logging.DEBUG if pytestconfig.option.debug_board else logging.INFO
    logging.getLogger("mpremote_path").setLevel(debug)
    logging.getLogger("unix_port").setLevel(debug)

    if port == "unix":
        # Run the micropython unix port behind a PTY to emulate a serial port.
        # This is useful for testing connections to micropython without a
        # real hardware device.
        # Where to find the micropython unix port and the initialisation script.
        tests_dir = Path(__file__).parent  # Base directory for the tests.
        unix_dir = tests_dir / "unix-micropython"
        micropython_path = unix_dir / "micropython"
        command = str(micropython_path) + ""  # " -i -m boot"

        working_dir = tmp_path_factory.mktemp("unix_micropython")
        unix_fs = working_dir / "fs"
        unix_fs.mkdir()  # Create the filesystem directory
        # shutil.copy(unix_dir / "boot.py", unix_fs)  # Copy boot.py to the fs

        with unix_port.run_pty_bridge(
            command, cwd=unix_fs, use_socat=use_socat
        ) as port:
            yield str(port)  # Return the path to the PTY as the serial port
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
    # Optimisation: wrap everything in a raw_repl so we are not slowed down by
    # entering and exiting the REPL for every command.
    with MPath.board.raw_repl():
        rm_recursive(MPath(board_test_dir))  # Clean up after previous test runs
        cwd = MPath.cwd()
        try:
            yield cwd
        finally:
            cwd.chdir()
    MPath.disconnect()  # Disconnect from the board


@pytest.fixture()
def testdir(root: MPath) -> Generator[MPath, None, None]:
    path, pwd = MPath(board_test_dir), MPath.cwd()
    try:
        yield path
    finally:
        pwd.chdir()


@pytest.fixture()
def testfolder(root: MPath) -> Generator[MPath, None, None]:
    "Create a test folder on the board and cd into it."
    pwd, path = MPath("~").expanduser(), MPath(board_test_dir)
    pwd.chdir()
    rm_recursive(path)
    path = path.resolve()
    path.mkdir()
    path.chdir()
    try:
        yield path
    finally:
        pwd.chdir()
    # rm_recursive(path)


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
