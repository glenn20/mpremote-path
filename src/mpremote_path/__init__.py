"""Provides the `MPRemotePath` class which provides a `pathlib.Path` compatible
interface to accessing and manipulating files on micropython boards via the
`mpremote` tool.
"""
# Copyright (c) 2021 @glenn20
# MIT License

__version__ = "0.0.1"

from .board import Board  # noqa: F401
from .mpremote_path import MPRemotePath  # noqa: F401
