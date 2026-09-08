"""Setup the logger functionality."""

import logging
import os

from rich.console import Console
from rich.highlighter import NullHighlighter
from rich.logging import RichHandler

# This is the logging message format that I like.
SIMPLE_LOG_FORMAT = "%(levelname)s:%(message)s"
SIMPLE_LOG_FORMAT_DEBUG = "%(levelname)s:%(name)s:%(message)s"

USE_SIMPLE_LOGGING: bool = os.getenv("SIMPLE_LOGGING", "0").lower() in {"1", "true", "yes"}

# This is where we log to in this module, following the standard of every module.
# I don't use the function so we can have this at the top
logger = logging.getLogger(__name__)


def _get_log_level_int(level: str | int) -> int:
    """Get the log level as an int."""
    if isinstance(level, int):
        return level
    return getattr(logging, level.upper(), logging.INFO)


def setup_logger_cli(verbosity: int, in_logger: logging.Logger | None = None) -> None:
    """Setup the logger from verbosity count from CLI."""
    log_level = logging.DEBUG if verbosity else logging.INFO
    setup_logger(log_level=log_level, in_logger=in_logger)


def setup_logger(log_level: str | int = logging.INFO, in_logger: logging.Logger | None = None) -> None:
    """Setup the logger, set configuration per logging_conf.

    Args:
        log_level: Logging level to set.
        in_logger: Logger to configure, useful for testing.
    """
    log_level_int = _get_log_level_int(log_level)

    if not in_logger:  # in_logger should only exist when testing with PyTest.
        in_logger = logging.getLogger()  # Get the root logger

    # If the logger doesn't have a console handler (root logger doesn't by default)
    if not any(isinstance(handler, (RichHandler, logging.StreamHandler)) for handler in in_logger.handlers):
        _add_console_handler(in_logger=in_logger, log_level_int=log_level_int)

    in_logger.setLevel(log_level_int)

    logger.info("Logger configuration set!")


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the name provided."""
    return logging.getLogger(name)


def _add_console_handler(in_logger: logging.Logger, log_level_int: int) -> None:
    """Add a console handler to the logger."""
    if not USE_SIMPLE_LOGGING:
        in_logger.addHandler(
            RichHandler(
                console=Console(),
                show_time=False,
                rich_tracebacks=True,
                highlighter=NullHighlighter(),
            )
        )
        return

    console_handler = logging.StreamHandler()
    # The debug format names the logger the line came from, which only helps
    # once you have asked for that much detail.
    fmt = SIMPLE_LOG_FORMAT_DEBUG if log_level_int <= logging.DEBUG else SIMPLE_LOG_FORMAT
    console_handler.setFormatter(logging.Formatter(fmt))
    in_logger.addHandler(console_handler)
