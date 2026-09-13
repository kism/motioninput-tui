"""Setup the logger functionality."""

import logging

from rich.highlighter import NullHighlighter
from rich.logging import RichHandler


def setup_logger_cli(verbosity: int) -> None:
    """Log to the console through Rich, at debug level once ``-v`` is given.

    A root logger that already has a handler keeps it, as ``basicConfig`` does.
    """
    handler = RichHandler(show_time=False, rich_tracebacks=True, highlighter=NullHighlighter())
    logging.basicConfig(format="%(message)s", handlers=[handler])
    logging.getLogger().setLevel(logging.DEBUG if verbosity else logging.INFO)
