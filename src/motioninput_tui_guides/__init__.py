"""Fetching the reference guides the parsers read.

Not part of the trainer. The dependencies live in the ``guides`` extra, and the
guides themselves are gitignored because they may not be redistributed.
"""

from .catalog import Guide, get_guide, load_guides
from .fetch import Result, Status, fetch_all, fetch_guide

__all__ = ["Guide", "Result", "Status", "fetch_all", "fetch_guide", "get_guide", "load_guides"]
