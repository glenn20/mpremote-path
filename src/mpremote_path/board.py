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
from functools import cached_property
from typing import (
    Any,
    Callable,
    Generator,
    TypeVar,
    cast,
)

import mpremote.transport_serial
from mpremote.transport_serial import SerialTransport, TransportError

from ._version import __version__

logger = logging.getLogger(__name__)

# Tolerance for time offset between host and board (seconds) if
# `set_clock=True` in `Board.check_clock()`.
board_time_offset_tolerance = 1.0  # seconds

default_baud_rate: int = 115200  # Default baud rate for serial connections


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


def make_board(*args: Any, **kwargs: Any) -> Board:
    """Wrapper around `Board()` for backward compatibility."""
    return Board(*args, **kwargs)


T = TypeVar("T", bound=Callable[..., Any])

_starttime: float = time.time()
_lastlogtime_ms: int = 0


# Decorator to log args and return values of calls to methods of a class
def logmethod(func: T, level: int = logging.DEBUG) -> T:
    def wrap(*args: Any, **kwargs: Any) -> Any:
        global _lastlogtime_ms, _starttime
        if logger.getEffectiveLevel() < level:
            return func(*args, **kwargs)
        arg_str = ", ".join(
            itertools.chain(
                (repr(arg) for arg in args[1:]),
                (f"{k}={v!r}" for k, v in kwargs.items()),
            )
        )
        cls = args[0]
        method = func.__name__
        msg = f"{cls}.{method}({arg_str})"
        now_ms = int((time.time() - _starttime) * 1000)
        delta_ms = now_ms - _lastlogtime_ms
        logger.log(
            level,
            f"{msg:40s} at {now_ms:4d}ms ({delta_ms:+4d}ms)",
        )
        _lastlogtime_ms = now_ms
        result = func(*args, **kwargs)
        now_ms = int((time.time() - _starttime) * 1000)
        delta_ms = now_ms - _lastlogtime_ms
        msg = f"{cls}.{method}() returned: {result!r}"
        logger.log(
            level,
            f"{msg:50s} ({delta_ms:+4d}ms)",
        )
        _lastlogtime_ms = now_ms
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

    _transport: SerialTransport
    _writer: Callable[[bytes], None] | None

    def __init__(
        self,
        port: str | SerialTransport,
        *,
        baud: int = 0,
        wait: int = 0,
        writer: Callable[[bytes], None] | None = None,
    ) -> None:
        """
        - `port` can be a string containing the full or abbreviated name of the
          serial port or an mpremote `SerialTransport` instance.
        - `baud` is the baud rate to use for the serial connection
        - `wait` is the number of seconds to wait for the board to become
          available when connecting.
        - `writer` is a function that will be called with the data received
          from the board. If not provided, the default writer will print to
          stdout.

        The serial port name may be the full device name (eg. "/dev/ttyUSB0")
        or a short name (eg. "u0").

        `baud` and `wait` are only used if `port` is a string."""
        baud = baud or default_baud_rate
        logger.debug(f"{__name__.split('.')[0]} version {__version__}")
        logger.debug(f"{self.__class__.__name__}({port!r}, baud={baud}, wait={wait})")
        self._transport = (
            port if isinstance(port, SerialTransport) else
            SerialTransport(device_long_name(port), baud, wait)
        )  # fmt: off
        self._writer = writer

    def close(self) -> None:
        """Close the connection to the micropython board."""
        if self._transport:
            self._transport.close()

    def __repr__(self) -> str:
        return f"Board({self.short_name!r})"

    @cached_property
    def epoch_offset(self) -> int:
        return self.calc_epoch_offset()

    @cached_property
    def clock_offset(self) -> float:
        return self.calc_clock_offset()

    @property
    def device_name(self) -> str:
        return self._transport.device_name

    @property
    def short_name(self) -> str:
        return device_short_name(self._transport.device_name).rsplit("/")[-1]

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
        interrupted = False
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
            interrupted = True
            raise  # Re-raise the KeyboardInterrupt up to the top level
        except TransportError as exc:
            self.writer(f"TransportError: {message!r}\r\n".encode())
            if len(exc.args) == 3:  # Raised by Pyboard.exec_()
                self.writer(exc.args[1])
                self.writer(exc.args[2])
            else:  # Others just include a single message
                self.writer(exc.args[0].encode())
            interrupted = True
            raise
        finally:
            # Only exit the raw_repl if we entered it with this instance
            if restore_repl and self._transport.in_raw_repl:
                self._transport.exit_raw_repl()
                if not interrupted:
                    self._transport.read_until(4, b">>> ")
                    self.writer(b">>> ")

    def soft_reset(self) -> None:
        """Perform a micropython soft reset of the board."""
        if self._transport.in_raw_repl:
            raise RuntimeError("Cannot reset micropython while in raw repl mode.")
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

    @logmethod
    def eval(self, expression: str) -> Any:
        """Execute `expression` on the micropython board and evaluate the
        output as a python expression on the local host."""
        with self.raw_repl(expression) as r:
            return r.eval(expression, True)

    @logmethod
    def eval_str(self, expression: str) -> str:
        """Execute `expression` on the micropython board and return the output
        as a python string."""
        with self.raw_repl(expression) as r:
            result = r.eval(expression, False)
            return result.decode()

    def exec_eval(self, code: str) -> Any:
        """Execute `code` on the micropython board and (safely) evaluate the
        printed output as a python expression on the local host."""
        response = self.exec(code, capture=True)
        return ast.literal_eval(response) if response else None

    @logmethod
    def fs_stat(self, filename: str) -> os.stat_result:
        """Wrapper around the mpremote `SerialTransport.fs_stat()` method.
        Converts the micropython timestamps to a unix timestamp by adding the
        epoch offset calculated by `Board.calc_epoch_offset()`. Note: does not
        correct for differences between the host clock and the micropython
        clock. Use `Board.check_clock(set_clock=True)` to synchronise the
        clocks."""
        with self.raw_repl() as r:
            stat = r.fs_stat(filename)
            return os.stat_result(  # Add epoch_offset to the micropython timestamps
                stat[:-3] + tuple((t + self.epoch_offset for t in stat[-3:]))
            )

    def calc_epoch_offset(self) -> int:
        """Calculate the epoch offset between the host and the board."""
        with self.raw_repl():
            self.exec("import time")
            gmt_now = time.gmtime(time.time())[:8]  # Use now as a reference time
            host_time = time.mktime((*gmt_now, -1))
            board_time = float(self.eval(f"time.mktime({gmt_now})"))
            return round(host_time - board_time)

    def calc_clock_offset(self) -> float:
        """Calculate the offset (seconds) of the board's RTC from the host clock."""
        with self.raw_repl():
            offset = self.epoch_offset  # Ensure we call this first to "import time"
            board_time = int(self.eval("time.time()"))
            local_time = time.time()
            return board_time + offset - local_time

    @logmethod
    def sync_clock(
        self,
        sync_time: time.struct_time | float | int | None = None,
        utc: bool = False,
    ) -> None:
        """Set the board's real-time clock to the host's time (utc or local).
        If `sync_time` is provided, the board clock will be set to that time.
        `sync_time` may be a `time.struct_time` object, a unix timestamp or None."""
        t: time.struct_time = (
            sync_time if isinstance(sync_time, time.struct_time) else
            time.gmtime(sync_time) if utc else
            time.localtime(sync_time)  # Use now if sync_time is None
        )  # fmt: off
        host_time = t.tm_year, t.tm_mon, t.tm_mday, 0, t.tm_hour, t.tm_min, t.tm_sec, 0
        self.exec(
            "import machine; "
            f"if hasattr(machine, 'RTC'): machine.RTC().datetime({host_time})"
        )

    @logmethod
    def check_clock(self, set_clock: bool = False, utc: bool = False) -> None:
        """Check the time on the board and save the epoch offset and clock
        offset between the host and the board (in seconds). Will sync the
        board's RTC to the host's time if `set_clock` is True. Will use UTC time
        if `utc` is True, otherwise local time will be used."""
        with self.raw_repl():  # Wrapper so we only enter/exit raw repl mode once
            # Calculate the offset (seconds) of the board clock from the host clock.
            if set_clock and abs(self.clock_offset) > board_time_offset_tolerance:
                self.sync_clock(utc=utc)
                del self.clock_offset  # Force recalculation of clock_offset
