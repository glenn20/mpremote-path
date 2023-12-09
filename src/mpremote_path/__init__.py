"""Provides the `MPRemotePath` class which is a `pathlib`-compatible wrapper
around the `SerialTransport` interface to a micropython board (from the
`mpremote` tool).
"""
# Copyright (c) 2021 @glenn20
# MIT License

__version__ = "0.0.1"

from .board import Board, Debug  # noqa: F401
from .mpremote_path import MPRemotePath  # noqa: F401
