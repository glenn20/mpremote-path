"""Provides the `Board` class for interacting with a micropython board via
mpremote.
"""

# For python<3.10: Allow method type annotations to reference enclosing class
from __future__ import annotations

import ast
import itertools
import logging
import os
import re
import sys
import time
from contextlib import contextmanager
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generator,
    Literal,
    TypeVar,
    cast,
    overload,
)

import mpremote.transport_serial
from mpremote.transport_serial import SerialTransport, TransportError

logger = logging.getLogger(__name__)

time_offset_tolerance = 1  # seconds


# Override the mpremote stdout writer which fails if stdout does not have a
# .buffer() method (eg. when running in a jupyter notebook)
def _mpath_stdout_write_bytes(b: bytes) -> None:
    b = b.replace(b"\x04", b"")
    sys.stdout.write(b.decode())
    sys.stdout.flush()


mpremote.transport_serial.stdout_write_bytes = _mpath_stdout_write_bytes


def device_long_name(device: str) -> str:
    """Return the full name of a serial port device file.
    `device` may be a port name (eg. "/dev/ttyUSB0") or a short name (eg. "u0")
    """
    device = re.sub(r"^u([0-9]+)$", r"/dev/ttyUSB\1", device)
    device = re.sub(r"^a([0-9]+)$", r"/dev/ttyACM\1", device)
    device = re.sub(r"^c([0-9]+)$", r"COM\1", device)
    return device


def device_short_name(device: str) -> str:
    """Return the short name of a serial port device file.
    `device` may be a full port name (eg. "/dev/ttyUSB0") or a short name (eg. "u0")
    """
    device = re.sub(r"^/dev/ttyUSB([0-9]+)$", r"u\1", device)
    device = re.sub(r"^/dev/ttyACM([0-9]+)$", r"a\1", device)
    device = re.sub(r"^/COM([0-9]+)$", r"c\1", device)
    return device


def make_board(
    port: str | Board | SerialTransport,
    baud: int = 115200,
    wait: int = 0,
    *,
    set_clock: bool = False,
    utc: bool = False,
    writer: Callable[[bytes], None] | None = None,
) -> Board:
    """Convenience function to return a `Board` instance from a serial port name
    or a `SerialTransport` object or an existing `Board` instance. The serial
    port name may be the full device name (eg. "/dev/ttyUSB0") or a short name
    (eg. "u0")."""
    board = (
        port
        if isinstance(port, Board)
        else (
            Board(port, writer=writer)
            if isinstance(port, SerialTransport)
            else Board(
                SerialTransport(device_long_name(port), baud, wait), writer=writer
            )
        )
    )
    board.check_clock(set_clock=set_clock, utc=utc)
    return board


T = TypeVar("T", bound=Callable[..., Any])


# Decorator to log args and return values of calls to methods of a class
def logmethod(func: T, level: int = logging.DEBUG) -> T:
    def wrap(*args: Any, **kwargs: Any) -> Any:
        if logger.getEffectiveLevel() < level:
            return func(*args, **kwargs)
        cls, method = args[0], func.__name__
        arg_str = ", ".join(
            itertools.chain(
                (repr(arg) for arg in args[1:]),
                (f"{k}={v!r}" for k, v in kwargs.items()),
            )
        )
        logger.log(level, f"{cls}.{method}({arg_str})")
        result = func(*args, **kwargs)
        logger.log(level, f"{cls}.{method}() returned: {result!r}")
        return result

    return cast(T, wrap)


class Board:
    """A class to represent a connection to a micropython board via mpremote.

    Access to the mpremote SerialTransport instance is mediated via the
    `raw_repl()` context manager, which ensures a raw repl is always active when
    in use and handles exceptions thrown by micropython: eg.
        `with board.raw_repl() as r: r.exec("print('Hello world')")`

    Board also provides convenience wrappers and methods for executing code on
    the micropython board:
        `exec()`, `eval()`, `eval_str()`, `exec_eval()`, `fs_stat()` and
        `check_clock()`.
    """

    def __init__(
        self, transport: SerialTransport, writer: Callable[[bytes], None] | None = None
    ) -> None:
        """Create a `Board` instance from an mpremote `SerialTransport` instance
        and, optionally, a writer function.
        The writer function will be passed to `SerialTransport.exec()`  to print
        output from code executed on the micropython board. If no writer
        function is provided, the default writer will print to stdout."""
        self._transport = transport
        self._writer = writer
        self.epoch_offset: int = 0
        self.clock_offset: int = 0

    def __repr__(self) -> str:
        return f"Board({self.short_name!r})"

    @property
    def device_name(self) -> str:
        return self._transport.device_name

    @property
    def short_name(self) -> str:
        return device_short_name(self._transport.device_name)

    def writer(self, data: bytes) -> None:
        """The writer function used by the mpremote SerialTransport instance."""
        if self._writer:
            self._writer(data)
        else:
            print(data.replace(b"\x04", b"").decode(), end="")

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
            raise  # Re-raise the KeyboardInterrupt up to the top level
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

    def soft_reset(self) -> None:
        self._transport.enter_raw_repl(soft_reset=True)
        self._transport.exit_raw_repl()

    # Convenience methods to execute stuff in the raw_repl on the micropython board
    @logmethod
    def exec(self, code: str, capture: bool = False) -> str:
        """Execute `code` on the micropython board,
        If `bool(capture)` is True, the output will be returned as a string,
        else it will be printed via Board.writer()."""
        with self.raw_repl(code) as r:
            return r.exec(code, None if capture else self.writer).decode().strip()

    if TYPE_CHECKING:

        @overload
        def _eval(self, expression: str, parse: Literal[False]) -> str: ...
        @overload
        def _eval(self, expression: str, parse: bool = False) -> Any: ...

    @logmethod
    def _eval(self, expression: str, parse: bool = False) -> Any:
        """Wrapper around the mpremote `SerialTransport.eval()` method."""
        with self.raw_repl(expression) as r:
            result = r.eval(expression, parse)
            if not parse and isinstance(result, bytes):
                return result.decode()
            else:
                return result

    def eval(self, expression: str) -> Any:
        """Execute `expression` on the micropython board and evaluate the
        output as a python expression on the local host."""
        return self._eval(expression, parse=True)

    def eval_str(self, expression: str) -> str:
        """Execute `expression` on the micropython board and return the output
        as a python string."""
        return self._eval(expression, parse=False)

    def exec_eval(self, code: str) -> Any:
        """Execute `code` on the micropython board and (safely) evaluate the
        printed output as a python expression on the local host."""
        response = self.exec(code, capture=True)
        return ast.literal_eval(response) if response else None

    def check_clock(self, set_clock: bool = False, utc: bool = False) -> None:
        """Check the time on the board and save the epoch offset and clock
        offset between the host and the board (in seconds). Will sync the
        board's RTC to the host's time if `set_clock` is True. Will use UTC time
        if `utc` is True, otherwise local time will be used."""
        with self.raw_repl():  # Wrapper so we only enter/exit raw repl mode once
            self.exec("import time, machine" if set_clock else "import time")
            # Calculate the epoch offset between the host and the board.
            tt = time.gmtime(time.time())[:8]  # Use now as a reference time
            self.epoch_offset = round(
                time.mktime((*tt, -1)) - int(self.eval(f"time.mktime({tt})"))
            )
            # Calculate the offset (seconds) of the board's RTC from the host clock.
            self.clock_offset = round(
                int(self.eval("time.time()")) + self.epoch_offset - time.time()
            )
            t = time.gmtime() if utc else time.localtime()
            t2 = (t.tm_year, t.tm_mon, t.tm_mday, 0, t.tm_hour, t.tm_min, t.tm_sec, 0)
            if set_clock and abs(self.clock_offset) > time_offset_tolerance:
                # Set the board's RTC to the host's time
                self.exec(f"machine.RTC().datetime({t2})")
                self.clock_offset = round(  # recalculate time offset
                    int(self.eval("time.time()")) + self.epoch_offset - time.time()
                )

    @logmethod
    def fs_stat(self, filename: str) -> os.stat_result:
        """Wrapper around the mpremote `SerialTransport.fs_stat()` method.
        Converts the micropython timestamps to a unix timestamp by adding the
        epoch offset calculated by `Board.check_clock()`. Note: does not correct
        for differences between the host clock and the micropython clock. Use
        `Board.check_clock(set_clock=True)` to synchronise the clocks."""
        with self.raw_repl() as r:
            stat = r.fs_stat(filename)
        if stat is None:
            raise FileNotFoundError(f"No such file or directory: '{self}'")
        return os.stat_result(  # Add epoch_offset to the micropython timestamps
            stat[:-3] + tuple((t + self.epoch_offset for t in stat[-3:]))
        )
