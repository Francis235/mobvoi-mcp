"""Mobvoi MCP package."""

from .client import Mobvoi
from .play import play, save, stream

# 指定此子包的公共API
__all__ = ["Mobvoi", "play", "save", "stream"]