"""Provides the "RemotePath" class which is a wrapper around the
PyBoardExtended interface to a micropython board (from the mpremote tool).
"""
# Copyright (c) 2021 @glenn20
# MIT License

__version__ = "0.0.1"

from .remote_path import RemotePath
from .board import Board, Debug
