"""Provides the `run_micropython()` context manager which runs the micropython
unix port behind a PTY to emulate a serial port. This is used by the tests to
communicate with the micropython unix port as if it were a hardware device
attached to a serial port.
"""

# Copyright (c) 2024 @glenn20
# MIT License

import logging
import logging.config
import os
import pty
import re
import select
import shutil
import subprocess
import sys
import termios
import time
from contextlib import contextmanager, suppress
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Generator

import yaml

# Where to find the micropython unix port and the initialisation script.
tests_dir = Path(__file__).parent  # Base directory for the tests.
unix_dir = tests_dir / "unix-micropython"
micropython = unix_dir / "micropython"
micropython_command = str(micropython) + " -i -m boot"
micropython_boot = unix_dir / "boot.py"  # Initialisation script.

log = logging.getLogger(__name__)


@contextmanager
def run_micropython(
    working_dir: Path,
    /,
    use_socat: bool = False,
) -> Generator[str, None, None]:
    """Run the micropython unix port behind a PTY to emulate a serial port.

    Runs the micropython unix port and returns the name of a PTY to use as the
    virtual serial port for communication with micropython. Input and output is
    relayed between the PTY and micropython by a "bridge" process.

    The initial implementation used the `socat` program to create the PTY and
    run the micropython unix port behind it.

    The default (and preferred) implementation uses a PTY bridge in pure python.
    This is more portable and does not require the socat program to be
    installed.

    Supported platforms are Linux and MacOS. Windows is not supported.
    """
    # Setup the working directories for running the unix port of micropython.
    unix_fs = working_dir / "fs"  # This will be the filesystem for micropython.
    unix_fs.mkdir()
    shutil.copy(micropython_boot, unix_fs)  # Copy boot.py to the fs directory

    # Run the micropython bridge process which starts the micropython unix port
    # behind a PTY.
    micropython = micropython_bridge_socat if use_socat else micropython_bridge_pty
    with micropython(micropython_command, working_dir) as pty:
        try:
            yield pty  # Return the name of the PTY as the serial port
        except KeyboardInterrupt:
            log.debug("Keyboard interrupt received in run_micropython().")
            raise


### The initial implementation using socat


@contextmanager
def micropython_bridge_socat(
    command: str, working_dir: Path
) -> Generator[str, None, None]:
    # Use socat to run the micropython unix port behind a PTY to emulate a
    # serial port connection to an actual device.
    unix_pty = working_dir / "pty"
    proc = subprocess.Popen(
        [
            "socat",
            f"PTY,link={unix_pty},rawer",
            f"EXEC:{command},pty,stderr,onlcr=0",
        ],
        cwd=working_dir / "fs",
    )
    if proc.returncode:
        raise RuntimeError("Failed to start socat process.")
    time.sleep(0.1)
    try:
        yield str(unix_pty)  # Return the path to the PTY as the serial port
    finally:
        proc.terminate()


### The preferred implementation using a PTY bridge in pure python


@contextmanager
def micropython_bridge_pty(command: str, cwd: Path) -> Generator[str, None, None]:
    """Run the micropython unix port using a PTY to emulate a serial port.
    Returns the name of the slave end of a PTY pair. The PTY emulates a serial
    port for communicating with a running instance of the micropython unix port.
    The "bridge" process runs the micropython unix port and relays data between
    the "serial port" PTY and the micropython process.
    """
    os.chdir(cwd)  # Change to the working directory
    # Create a new PTY master-slave pair.
    bridge_pty, serial_port_pty = pty.openpty()  # Open the new PTY
    pty_set_rawer(serial_port_pty)  # Emulate the `rawer` option of socat
    serial_port_name = os.ttyname(serial_port_pty)  # Get the name of the PTY
    os.close(serial_port_pty)

    # Start the bridge process which will run the micropython unix port.
    bridge_pid = os.fork()
    if bridge_pid == 0:
        # Child process - the Bridge process
        log.debug(
            f"Bridge process: pid={os.getpid()}, pty={bridge_pty} ({serial_port_name})."
        )
        os.chdir(cwd / "fs")  # Change to the micropython fs directory
        # Run micropython and forward data to/from `serial_port_name`.
        run_micropython_subprocess(command, bridge_pty)
        log.debug("Bridge process: Exiting.")
        sys.exit()  # Exit the subprocesses.

    # Parent process - the main process
    try:
        yield serial_port_name  # Return the name of the PTY as the serial port
    finally:
        # Close the PTY and wait for the bridge process to finish.
        close_pty_subprocess(bridge_pty, bridge_pid)


def run_micropython_subprocess(command: str, bridge_pty: int) -> None:
    """Start the micropython unix port subprocess attached to a PTY.
    Return the child PID and file descriptor of the PTY."""
    argv = command.split()
    micropython_path = Path(argv[0]).resolve()
    argv = [argv[0].rsplit("/")[-1]] + argv[1:]  # Use abbreviated command name

    micropython_pid, micropython_pty = pty.fork()
    if micropython_pid == 0:
        # Child process - run the micropython command
        # pytest redirects sys.stdin, so we need to check sys.__stdin__
        pty_set_micropython((sys.__stdin__ or sys.stdin).fileno())
        os.execv(micropython_path, argv)  # Run micropython

    # Parent process - the Bridge process
    log.debug(f"Micropython process: pid={micropython_pid}, pty={micropython_pty}.")
    try:
        # Relay data between the PTY and the micropython process till it exits
        pty_relay(bridge_pty, micropython_pty)
    except KeyboardInterrupt:
        log.debug("Keyboard interrupt received in bridge process.")
    finally:
        close_pty_subprocess(micropython_pty, micropython_pid)


def pty_relay(bridge_pty: int, micropython_pty: int) -> int:
    """Relay data between two file descriptors.
    Copies data as it is available from each pty to the other and vice
    versa. This will be used by `run_micropython_subprocess` to relay data
    between the PTY and the micropython process.
    Returns 0 when the client closes the connection to `bridge_pty`.
    Returns 0 when micropython closes the connection to `micropython_pty`."""
    poll = select.poll()
    poll.register(bridge_pty, select.POLLIN | select.POLLHUP)
    poll.register(micropython_pty, select.POLLIN | select.POLLHUP)

    other_pty = {bridge_pty: micropython_pty, micropython_pty: bridge_pty}
    connected = {bridge_pty: False, micropython_pty: True}

    # Relay data between the two file descriptors
    while True:
        for fd, ev in poll.poll():  # Wait for data to be available
            if ev & select.POLLIN:
                if data := os.read(fd, 1024):
                    log.debug(f"{fd} -> {other_pty[fd]}: {data!r}")
                    os.write(other_pty[fd], data)
                    if not connected[fd]:
                        log.debug(f"Client connected to bridge PTY {fd}.")
                        connected[fd] = True

            if ev & select.POLLHUP:
                if fd and connected[fd]:
                    log.debug(f"PTY {fd} has been closed by peer.")
                    return 0
                else:
                    time.sleep(0.5)  # Keep waiting for the PTY to be opened.


def close_pty_subprocess(pty_fd: int, child_pid: int) -> None:
    """Close the PTY and wait for the child process to finish.
    Send SIGTERM to the child process if it is still running after 2 seconds."""
    log.debug(f"Closing PTY {pty_fd}.")
    os.close(pty_fd)
    for _ in range(20):  # Wait up to 2 seconds for the child process to exit
        try:
            pid, status = os.waitpid(child_pid, os.WNOHANG)
            if pid and os.WIFEXITED(status):
                return
        except ChildProcessError:
            return  # Child process has already exited
        time.sleep(0.1)
    # If the bridge process is still running, terminate it.
    log.debug(f"Terminating child process {child_pid}.")
    with suppress(OSError):
        os.kill(child_pid, 15)  # Send SIGTERM to the child process
        os.waitpid(child_pid, 0)  # Wait for the child to finish


def pty_set_micropython(fd: int) -> None:
    """Initialise the PTY for use by micropython.
    This fixes up the CR/NL translation for compatibility with mpremote and others."""
    tc = termios.tcgetattr(fd)
    tc[1] &= ~termios.ONLCR  # Disable CR/NL translation
    termios.tcsetattr(fd, termios.TCSAFLUSH, tc)


def pty_set_rawer(fd: int) -> None:
    """Initialise the PTY for use as the emulated serial port.
    Sets the PTY to `rawer` mode (this is the same as the mode used by socat)."""
    tc = termios.tcgetattr(fd)  # Get the current terminal attributes
    # Set the PTY terminal attributes to emulate the `rawer` option of socat
    tc[0] = 0  # Input flags
    tc[1] = 0  # Output flags
    tc[2] = termios.CREAD | termios.CS8  # Control flags
    tc[3] = 0  # Local flags
    tc[6][termios.VMIN] = 1
    tc[6][termios.VTIME] = 20  # Read timeout in tenths of a second
    termios.tcsetattr(fd, termios.TCSAFLUSH, tc)  # Set the attributes for the PTY


# Find a valid baud rate for the given baud rate.
def get_baud_rate(requested_baud: int) -> tuple[int, int]:
    """Find the highest baud rate <= requested_baud from the available baud
    rates. Returns a tuple of (baud_rate, termios_value) where baud_rate is the
    baud rate in bits per second and termios_value is the value to be passed to
    the tcsetattr() function."""
    available_baud_rates: Generator[tuple[int, int], None, None] = (
        # Baud rates are defined as B<rate> in the termios module.
        (int(k[1:]), v)
        for k, v in termios.__dict__.items()
        if re.match(r"B[0-9]+$", k)
    )
    return max(
        available_baud_rates,
        key=lambda x: x[0] if x[0] <= requested_baud else 0,
    )


def main() -> None:
    logging_config = tests_dir / "logging.yaml"  # Logging configuration file.

    logging.config.dictConfig(yaml.safe_load(logging_config.read_text()))

    with TemporaryDirectory() as working_dir:
        try:
            with run_micropython(Path(working_dir), use_socat=False) as pty:
                print(f"Running micropython on {pty}...")
                os.waitpid(-1, 0)  # Wait for the child process to finish
        except KeyboardInterrupt:
            log.debug("Keyboard interrupt received in main process, exiting...")


if __name__ == "__main__":
    main()
