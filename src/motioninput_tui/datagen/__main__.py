"""Regenerate the packaged roster data from the reference FAQs.

Run from the repository root::

    python -m motioninput_tui.datagen
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from motioninput_tui.games.loader import write_game
from motioninput_tui.games.rulesets import GAME_SPECS
from motioninput_tui.utils.logger import get_logger, setup_logger_cli

from . import hsf2, sfa3, sfiii3

logger = get_logger(__name__)

PARSERS = {"hsf2": hsf2.parse, "sfa3": sfa3.parse, "sfiii3": sfiii3.parse}


def _get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="motioninput-tui-datagen", description=__doc__)
    parser.add_argument("--references", type=Path, default=Path("references"), help="Directory of reference FAQs.")
    parser.add_argument("--show-skipped", action="store_true", help="List moves that could not be normalised.")
    parser.add_argument("-v", action="count", default=0, help="Increase verbosity.")
    return parser.parse_args()


def main() -> int:
    """Parse every reference file and write the packaged data."""
    args = _get_args()
    setup_logger_cli(args.v)

    exit_code = 0
    for key, spec in GAME_SPECS.items():
        source = args.references / Path(spec.reference).name
        if not source.is_file():
            logger.error("Missing reference file: %s. Fetch it with: python -m motioninput_tui_guides", source)
            exit_code = 1
            continue

        characters, report = PARSERS[key](source.read_text(encoding="utf-8", errors="replace"))
        if not characters:
            logger.error("%s: parsed nothing from %s", spec.short_name, source)
            exit_code = 1
            continue

        path = write_game(key, characters)
        logger.info("%-9s %s -> %s", spec.short_name, report.summary(), path.name)
        if args.show_skipped:
            for skipped in report.skipped:
                logger.info("  skipped %s", skipped)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
