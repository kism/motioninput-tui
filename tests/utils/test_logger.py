"""Logger unit tests."""

import logging
import subprocess  # ruff: ignore[suspicious-subprocess-import] - only ever runs this interpreter
import sys

# In a fresh interpreter, since pytest's own handlers on the root logger would
# make basicConfig a no-op here.
_CHECK = """
import logging
from motioninput_tui.utils.logger import setup_logger_cli
root = logging.getLogger()
setup_logger_cli(1)
verbose = root.level
setup_logger_cli(0)
print(verbose, root.level, [type(handler).__name__ for handler in root.handlers])
"""


def test_verbosity_sets_the_level_on_one_rich_handler() -> None:
    result = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] - a fixed script
        [sys.executable, "-c", _CHECK], capture_output=True, text=True, check=True
    )
    assert result.stdout.strip() == f"{logging.DEBUG} {logging.INFO} ['RichHandler']"
