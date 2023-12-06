# For python<3.10: Allow method type annotations to reference enclosing class
from __future__ import annotations

import sys
from contextlib import contextmanager
from enum import IntFlag
from typing import Any, Generator

import mpremote.transport_serial
from mpremote.transport_serial import SerialTransport, TransportError


def my_stdout_write_bytes(b: bytes):
    b = b.replace(b"\x04", b"")
    sys.stdout.write(b.decode())
    sys.stdout.flush()


# Override the mpremote stdout writer which fails if stdout does not have a
# .buffer() method (eg. when running in a jupyter notebook)
mpremote.transport_serial.stdout_write_bytes = my_stdout_write_bytes


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

    # Methods to execute stuff in the raw_repl on the micropython board
    def exec(self, code: bytes | str) -> str:
        """Execute `code` on the micropython board and return the output as a
        string."""
        if self.debug & Debug.EXEC:
            print(f"Board.exec(): code = {code!r}")
        with self.raw_repl(code) as r:
            response: str = r.exec(code, self.writer).decode().strip()
        if self.debug & Debug.EXEC:
            print(f"Board.exec(): resp = {response!r}")
        return response

    def _eval(self, code: bytes | str, parse=False) -> Any:
        """Wrapper around the mpremote `SerialTransport.eval()` method."""
        if self.debug & Debug.EXEC:
            print(f"Board.eval(): code = {code!r}")
        with self.raw_repl(code) as r:
            response = r.eval(code, parse)
        if self.debug & Debug.EXEC:
            print(f"Board.eval(): resp = {response!r}")
        return response

    def eval(self, code: bytes | str) -> Any:
        """Execute `code` on the micropython board and evaluate the output as a
        python expression."""
        return self._eval(code, parse=True)

    def eval_str(self, code: bytes | str) -> str:
        """Execute `code` on the micropython board and return the output as a
        python string."""
        return self._eval(code, parse=False)
