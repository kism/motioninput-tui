"""Terminal identification, latency warnings and keyboard protocol support."""

from .detect import Speed, TerminalInfo, detect
from .kitty import query_support

__all__ = ["Speed", "TerminalInfo", "detect", "query_support"]
