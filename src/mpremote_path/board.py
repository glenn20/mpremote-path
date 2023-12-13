# For python<3.10: Allow method type annotations to reference enclosing class
from __future__ import annotations

import ast
import os
import re
import sys
import time
from contextlib import contextmanager
from enum import IntFlag
from typing import Any, Generator

import mpremote.transport_serial
from mpremote.transport_serial import SerialTransport, TransportError

time_offset_tolerance = 1  # seconds


def my_stdout_write_bytes(b: bytes):
    b = b.replace(b"\x04", b"")
    sys.stdout.write(b.decode())
    sys.stdout.flush()


# Override the mpremote stdout writer which fails if stdout does not have a
# .buffer() method (eg. when running in a jupyter notebook)
mpremote.transport_serial.stdout_write_bytes = my_stdout_write_bytes


def make_transport(
    device: str, baudrate: int = 115200, wait: int = 0
) -> SerialTransport:
    """Create a `SerialTransport` instance on the given serial port."""
    port: str = device
    port = re.sub(r"^u([0-9]+)$", r"/dev/ttyUSB\1", port)
    port = re.sub(r"^a([0-9]+)$", r"/dev/ttyACM\1", port)
    port = re.sub(r"^c([0-9]+)$", r"COM\1", port)
    dev = port
    dev = re.sub(r"^/dev/ttyUSB([0-9]+)$", r"u\1", dev)
    dev = re.sub(r"^/dev/ttyACM([0-9]+)$", r"a\1", dev)
    dev = re.sub(r"^/COM([0-9]+)$", r"c\1", dev)
    return SerialTransport(port, baudrate, wait)


def make_board(
    port: str | Board | SerialTransport, baud: int = 115200, wait: int = 0
) -> Board:
    """Return a `Board` instance from a serial port name or a `SerialTransport`
    object or an existing `Board` instance."""
    return (
        port
        if isinstance(port, Board)
        else Board(port)
        if isinstance(port, SerialTransport)
        else Board(make_transport(port, baud, wait))
    )


class Debug(IntFlag):
    NONE = 0
    EXEC = 1
    FILES = 2


class Board:
    """A class to represent a connection to a micropython board via mpremote.

    Access to the mpremote SerialTransport instance is mediated via the
    `raw_repl()` context manager, which ensures a raw repl is always active when
    in use: eg.
        `with board.raw_repl() as r: r.exec("print('Hello world')")`

    Also provides convenience wrappers and methods for executing code on the
    micropython board:
        `exec()`, `eval()`, `eval_str()`.
    """

    def __init__(self, transport: SerialTransport) -> None:
        self._transport = transport
        self.debug: Debug = Debug.NONE
        self.epoch_offset: int = 0
        self.clock_offset: int = 0

    def writer(self, b: bytes) -> None:
        """The writer function used by the mpremote SerialTransport instance."""
        print(b.decode(), end="")

    @contextmanager
    def raw_repl(self, message: Any = "") -> Generator[SerialTransport, None, None]:
        """A context manager for the mpremote `raw_repl`.
        These may be nested, but only the outermost will enter/exit the
        `raw_repl`.
        """
        restore_repl = False
        try:
            # We can nest raw_repl() managers - only enter raw repl if necessary
            if not self._transport.in_raw_repl:
                restore_repl = True
                self._transport.enter_raw_repl(soft_reset=False)
            yield self._transport
        except KeyboardInterrupt:
            # ctrl-C twice: interrupt any running program
            print("Interrupting command on board.")
            self._transport.serial.write(b"\r\x03\x03")
            raise
        except TransportError as exc:
            self.writer(f"TransportError: {message!r}\r\n".encode())
            if len(exc.args) == 3:  # Raised by Pyboard.exec_()
                self.writer(exc.args[1])
                self.writer(exc.args[2])
            else:  # Others just include a single message
                self.writer(exc.args[0].encode())
            raise
        finally:
            # Only exit the raw_repl if we entered it with this instance
            if restore_repl and self._transport.in_raw_repl:
                self._transport.exit_raw_repl()
                self._transport.read_until(4, b">>> ")

    def soft_reset(self):
        self._transport.enter_raw_repl(soft_reset=True)
        self._transport.exit_raw_repl()

    # Methods to execute stuff in the raw_repl on the micropython board
    def exec(self, code: bytes | str, capture: bool = False) -> str:
        """Execute `code` on the micropython board and return the output as a
        string."""
        if self.debug & Debug.EXEC:
            print(f"Board.exec(): code = {code!r}")
        with self.raw_repl(code) as r:
            response: str = (
                r.exec(code, None if capture else self.writer).decode().strip()
            )
        if self.debug & Debug.EXEC:
            print(f"Board.exec(): resp = {response!r}")
        return response

    def _eval(self, expression: bytes | str, parse=False) -> Any:
        """Wrapper around the mpremote `SerialTransport.eval()` method."""
        if self.debug & Debug.EXEC:
            print(f"Board.eval(): code = {expression!r}")
        with self.raw_repl(expression) as r:
            response = r.eval(expression, parse)
        if self.debug & Debug.EXEC:
            print(f"Board.eval(): resp = {response!r}")
        return response

    def eval(self, expression: bytes | str) -> Any:
        """Execute `expression` on the micropython board and evaluate the
        output as a python expression."""
        return self._eval(expression, parse=True)

    def eval_str(self, expression: bytes | str) -> str:
        """Execute `expression` on the micropython board and return the output
        as a python string."""
        return self._eval(expression, parse=False)

    def exec_eval(self, code: bytes | str) -> Any:
        """Execute `code` on the micropython board and evaluate the printed
        output as a python expression."""
        return ast.literal_eval(self.exec(code, capture=True))

    def check_time(self, sync_clock: bool = False, utc: bool = False) -> None:
        """Check the time on the board and return the epoch offset and clock offset
        in seconds. Will sync the board's RTC to the host's time if `sync` is True.
        Will use UTC time if `utc` is True, otherwise local time will be used."""
        with self.raw_repl():  # Make sure we are in raw repl mode
            self.exec("import time, machine" if sync_clock else "import time")
            # Calculate the epoch offset between the host anf the board's RTC.
            tt = time.gmtime(time.time())[:8]  # Use now as a reference time
            self.epoch_offset = round(
                time.mktime((*tt, -1)) - int(self.eval(f"time.mktime({tt})"))
            )
            self.clock_offset = round(
                time.time() - (int(self.eval("time.time()")) + self.epoch_offset)
            )
            t = time.gmtime() if utc else time.localtime()
            t2 = (t.tm_year, t.tm_mon, t.tm_mday, 0, t.tm_hour, t.tm_min, t.tm_sec, 0)
            if sync_clock and abs(self.clock_offset) > time_offset_tolerance:
                self.exec(f"machine.RTC().datetime({t2})")
                self.clock_offset = round(  # recalculate time offset
                    time.time() - (int(self.eval("time.time()")) + self.epoch_offset)
                )

    def fs_stat(self, filename: str) -> os.stat_result:
        """Wrapper around the mpremote `SerialTransport.fs_stat()` method.
        Converts the micropython timestamps to a unix timestamp by adding the
        epoch offset calculated by `check_time()`."""
        with self.raw_repl() as r:
            stat = r.fs_stat(filename)
        if stat is None:
            raise FileNotFoundError(f"No such file or directory: '{self}'")
        stat = os.stat_result(
            stat[:-3] + tuple((t + self.epoch_offset for t in stat[-3:]))
        )
        return stat
