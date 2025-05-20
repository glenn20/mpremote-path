import os
import platform
import pty
import select
import shutil
import subprocess
import sys
import termios
import time
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Generator, Optional

# Where to find the micropython unix port and the initialisation script.
tests_dir = Path(__file__).parent  # Base directory for the tests.
unix_dir = tests_dir / "unix-micropython"
micropython = unix_dir / "micropython"
micropython_command = str(micropython) + " -i -m boot"
micropython_boot = unix_dir / "boot.py"  # Initialisation script.


# Install the socat package if running as a Github Action.
def install_socat() -> None:
    osname = platform.system()
    print(f"Running on {osname!r} in Github Actions.")
    if osname == "Linux":
        print("Installing socat ubuntu package...")
        subprocess.run("sudo apt-get install socat".split(), check=True)
    else:
        raise RuntimeError(f"Micropython unix port not supported on {osname}.")


def pty_set_rawer(fd: int) -> None:
    tc = termios.tcgetattr(fd)  # Get the current terminal attributes
    # Set the PTY terminal attributes to emulate the `rawer` option of socat
    tc[0] = 0  # Input flags
    tc[1] = 0  # Output flags
    tc[2] = termios.CREAD | termios.CS8  # Control flags
    tc[3] = 0  # Local flags
    tc[4] = termios.B2000000  # Input speed
    tc[5] = termios.B2000000  # Output speed
    tc[6][termios.VMIN] = 1
    tc[6][termios.VTIME] = 0
    termios.tcsetattr(fd, termios.TCSAFLUSH, tc)  # Set the attributes for the PTY


def pty_relay(fd1: int, fd2: int, child_pid: int) -> int:
    # Relay data between the two file descriptors
    poll = select.poll()
    poll.register(fd1, select.POLLIN)
    poll.register(fd2, select.POLLIN)

    def pty_copy(src: int, dst: int) -> None:
        data = os.read(src, 1024)
        if data:
            os.write(dst, data)

    start_time = time.time()
    while time.time() - start_time < 600:
        # Read from the PTY and write to the master end
        for fd, ev in poll.poll(1000):  # Wait for data to be available
            if ev & select.POLLIN:
                if fd == fd1:
                    pty_copy(fd1, fd2)
                elif fd == fd2:
                    pty_copy(fd2, fd1)
                # Check if the child process has exited
        pid, status = os.waitpid(child_pid, os.WNOHANG)
        if pid > 0:
            return status
    return -1  # Indicate that the process is still running


@contextmanager
def micropython_bridge_pty(
    command: str, cwd: Optional[Path] = None
) -> Generator[tuple[int, str], None, None]:
    """Run the micropython unix port using a PTY to emulate a serial port."""
    relay_fd, relay_pty = pty.openpty()  # Open a new PTY
    print(f"Relay pty: {os.ttyname(relay_pty)}")
    pty_set_rawer(relay_pty)  # Set the PTY to emulate the `rawer` option of socat

    relay_pid = os.fork()
    if relay_pid == 0:
        # Child process - the Relay process
        micropy_pid, micropy_fd = pty.fork()
        if micropy_pid == 0:
            # Micropython Child process
            print(f"Micropython Child process: {os.getpid()}")
            print(
                f"Starting {command.rsplit('/')[-1]} on {os.ttyname(sys.stdin.fileno())}..."
            )
            if cwd:
                os.chdir(cwd / "fs")  # Change to the working directory
            argv = command.split()
            fd = sys.stdin.fileno()
            tc = termios.tcgetattr(fd)
            tc[1] &= ~termios.ONLCR  # Disable translation of LF to CRLF
            tc[4] = termios.B2000000  # Input speed
            tc[5] = termios.B2000000  # Output speed
            termios.tcsetattr(fd, termios.TCSAFLUSH, tc)
            os.execv(argv[0], argv)
        else:
            # Parent process - the Relay process
            print(f"Relay process: {os.getpid()}")
            status = 0
            try:
                status = pty_relay(relay_fd, micropy_fd, micropy_pid)
                print(f"Micropython exited with status {status}.")
            except KeyboardInterrupt:
                print("Keyboard interrupt received, exiting...")
            finally:
                os.close(relay_fd)
                os.close(relay_pty)
                os.close(micropy_fd)
                try:
                    os.kill(micropy_pid, 15)  # Send SIGTERM to the child process
                    os.waitpid(micropy_pid, 0)  # Wait for the child to finish
                except OSError:
                    pass
                sys.exit(status)  # Exit with status of the micropython child process
    else:
        # Parent process
        yield relay_pid, os.ttyname(relay_pty)
        os.close(relay_fd)
        os.close(relay_pty)
        try:
            os.kill(relay_pid, 15)  # Send SIGTERM to the child process
            os.waitpid(relay_pid, 0)  # Wait for the child to finish
        except OSError:
            pass
        print("Relay process finished.")


@contextmanager
def micropython_bridge_socat(
    command: str, working_dir: Path
) -> Generator[tuple[int, str], None, None]:
    # Use socat to run the micropython unix port behind a PTY to emulate a
    # serial port connection to an actual device.
    unix_pty = working_dir / "pty"
    proc = subprocess.Popen(
        [
            "socat",
            f"PTY,link={unix_pty},rawer,b4000000",
            f"EXEC:{command},pty,stderr,onlcr=0,b4000000",
        ],
        cwd=working_dir / "fs",
    )
    if proc.returncode:
        raise RuntimeError("Failed to start socat process.")
    time.sleep(0.1)
    yield proc.pid, str(unix_pty)  # Return the path to the PTY as the serial port
    proc.terminate()


@contextmanager
def run_micropython(
    working_dir: Path, use_socat: bool = False
) -> Generator[str, None, None]:
    """Run the micropython unix port using socat to emulate a serial port."""
    # Setup the working directories for running the unix port of micropython.
    unix_fs = working_dir / "fs"  # This will be the filesystem for micropython.
    unix_fs.mkdir()
    shutil.copy(micropython_boot, unix_fs)  # Copy boot.py to the fs directory

    if use_socat:
        with micropython_bridge_socat(micropython_command, working_dir) as (_pid, pty):
            yield pty  # Return the path to the PTY as the serial port
    else:
        with micropython_bridge_pty(micropython_command, working_dir) as (_pid, pty):
            yield pty


def main() -> None:
    with TemporaryDirectory() as working_dir:
        with run_micropython(Path(working_dir), use_socat=False) as pty:
            print(f"Running micropython on {pty}...")
            try:
                os.waitpid(-1, 0)  # Wait for the child process to finish
            except KeyboardInterrupt:
                print("Keyboard interrupt received, exiting...")


if __name__ == "__main__":
    main()
