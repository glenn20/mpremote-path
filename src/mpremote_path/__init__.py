"""Provides the `MPRemotePath` class which provides a `pathlib.Path` compatible
interface to accessing and manipulating files on micropython boards via the
`mpremote` tool.

Dependencies: - `mpremote.py` for access to serial-attached ESP32 devices.
"""

# Copyright (c) 2023-2024 @glenn20
# MIT License

from mpremote_path._version import __version__ as __version__
from mpremote_path.board import Board as Board
from mpremote_path.mpremote_path import MPRemotePath as MPRemotePath
from mpremote_path.mpremote_path import is_wildcard_pattern as is_wildcard_pattern
from mpremote_path.mpremote_path import mpremotepath as mpremotepath
