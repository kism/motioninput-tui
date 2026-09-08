"""Logger unit tests."""

import logging
from typing import TYPE_CHECKING

import pytest

from motioninput_tui.utils.logger import setup_logger, setup_logger_cli

if TYPE_CHECKING:
    from collections.abc import Generator
else:
    Generator = object

ONE_HANDLER = 1


@pytest.fixture
def logger() -> Generator:
    """Logger to use in unit tests, including cleanup."""
    logger = logging.getLogger("TEST_LOGGER")

    assert len(logger.handlers) == 0  # Check the logger has no handlers

    yield logger

    # Reset the test object since it will persist.
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()


def test_handler_console_added(logger: logging.Logger) -> None:
    """Test logging console handler."""
    setup_logger(log_level="INFO", in_logger=logger)
    assert len(logger.handlers) == ONE_HANDLER

    # TEST: If a console handler exists, another one shouldn't be created
    setup_logger(log_level="INFO", in_logger=logger)
    assert len(logger.handlers) == ONE_HANDLER


def test_an_unknown_level_name_falls_back_to_info(logger: logging.Logger) -> None:
    setup_logger(log_level="NONSENSE", in_logger=logger)
    assert logger.getEffectiveLevel() == logging.INFO


@pytest.mark.parametrize("log_level", [logging.INFO, logging.DEBUG])
def test_simple_logging_console_handler(
    logger: logging.Logger, monkeypatch: pytest.MonkeyPatch, log_level: int
) -> None:
    """Test the USE_SIMPLE_LOGGING path uses a plain StreamHandler."""
    monkeypatch.setattr("motioninput_tui.utils.logger.USE_SIMPLE_LOGGING", True)
    setup_logger(log_level=log_level, in_logger=logger)
    assert len(logger.handlers) == ONE_HANDLER
    assert isinstance(logger.handlers[0], logging.StreamHandler)


@pytest.mark.parametrize(
    ("verbosity", "expected_level"),
    [
        (0, logging.INFO),  # <no -v>
        (1, logging.DEBUG),  # -v
        (2, logging.DEBUG),  # -vv, the same: nothing logs below debug
    ],
)
def test_logger_setup_cli(logger: logging.Logger, verbosity: int, expected_level: int) -> None:
    setup_logger_cli(verbosity=verbosity, in_logger=logger)
    assert logger.getEffectiveLevel() == expected_level
