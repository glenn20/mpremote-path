import json
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


mpremote.transport_serial.stdout_write_bytes = my_stdout_write_bytes


class Debug(IntFlag):
    NONE = 0
    EXEC = 1
    FILES = 2


class Board(SerialTransport):
    def __init__(
        self,
        port: str,
        baudrate: int = 115200,
        wait: int = 0,
        exclusive: bool = True,
    ) -> None:
        super().__init__(port, baudrate, wait, exclusive)
        self.debug: Debug = Debug.NONE

    def writer(self, b: bytes) -> None:
        print(b.decode())

    # A context manager for the raw_repl - not re-entrant
    @contextmanager
    def raw_repl(self, message: Any = "") -> Generator[None, None, None]:
        """A context manager for the mpremote raw_repl.
        These may be nested, but only the outermost will enter/exit the raw_repl.
        """
        restore_repl = False
        try:
            # We can nest raw_repl() managers - only enter raw repl if necessary
            if not self.in_raw_repl:
                restore_repl = True
                self.enter_raw_repl(soft_reset=False)
            yield
        except KeyboardInterrupt:
            # ctrl-C twice: interrupt any running program
            print("Interrupting command on board.")
            self.serial.write(b"\r\x03\x03")
            raise
        except TransportError as exc:
            self.writer(f"TransportError: {message!r}\r\n".encode())
            if len(exc.args) == 3:  # Raised by Pyboard.exec_()
                self.writer(exc.args[1])
                self.writer(exc.args[2])
            else:  # Others just include a single message
                self.writer(exc.args[0].encode())
        finally:
            # Only exit the raw_repl if we entered it with this instance
            if restore_repl and self.in_raw_repl:
                self.exit_raw_repl()
                self.read_until(4, b">>> ")

    # Execute stuff on the micropython board
    def exec2(self, code: bytes | str, silent: bool = True) -> str:
        "Execute some code on the micropython board."
        response: str = ""
        if self.debug & Debug.EXEC:
            print(f"Board.exec(): code = {code!r}")
        with self.raw_repl(code):
            writer = self.writer if not silent else None
            response = super().exec(code, writer).decode().strip()
        if self.debug & Debug.EXEC:
            print(f"Board.exec(): resp = {response}")
        return response

    def eval_json(self, code: str) -> Any:
        """Execute code on board and interpret the output as json.
        Single quotes (') in output will be changed to " before processing."""
        response = self.exec2(code)
        # Safer to use json to construct objects rather than eval().
        # Exceptions will be caught at the top level.
        return json.loads(response.replace("'", '"'))

    def getcwd(self) -> str:
        return self.eval_json("print(repr(os.getcwd()))")
