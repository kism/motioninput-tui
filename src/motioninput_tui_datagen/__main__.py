"""Regenerate the packaged roster data from the reference FAQs.

Run from the repository root::

    python -m motioninput_tui_datagen

This lives outside the ``motioninput_tui`` package on purpose, so it is not
shipped in the wheel. It is a development tool for regenerating roster data from
the guides fetched by ``python -m motioninput_tui_guides``.
"""

import argparse
import logging
import sys
from pathlib import Path

from motioninput_tui.games.rulesets import GAME_SPECS
from motioninput_tui.utils.logger import setup_logger_cli

from .commands import apply_command_overrides
from .names import apply_overrides
from .parsers import hsf2, kof98, kof2001, lastbld2, samsh5sp, samsho2, sfa3, sfiii3, usfiv
from .roster import write_game
from .summary import print_summary

logger = logging.getLogger(__name__)

PARSERS = {
    "hsf2": hsf2.parse,
    "sfa3": sfa3.parse,
    "sfiii3": sfiii3.parse,
    "kof98": kof98.parse,
    "kof2001": kof2001.parse,
    "lastbld2": lastbld2.parse,
    "samsho2": samsho2.parse,
    "samsh5sp": samsh5sp.parse,
    "usfiv": usfiv.parse,
}


def _get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python -m motioninput_tui_datagen", description=__doc__)
    parser.add_argument("--references", type=Path, default=Path("references"), help="Directory of reference FAQs.")
    parser.add_argument("--show-skipped", action="store_true", help="List moves that could not be normalised.")
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a per-character breakdown of the roster data on disk and exit, without regenerating.",
    )
    parser.add_argument("-v", action="count", default=0, help="Increase verbosity.")
    return parser.parse_args()


def main() -> int:
    """Parse every reference file and write the packaged data."""
    args = _get_args()
    setup_logger_cli(args.v)

    if args.summary:
        return print_summary()

    exit_code = 0
    for key, spec in GAME_SPECS.items():
        if not spec.reference:  # The input display has no roster to generate.
            continue
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

        # Names first: a command override is keyed by the character key the
        # roster ends up with, not the one the guide happened to produce.
        named = apply_overrides(key, characters)
        path = write_game(key, apply_command_overrides(key, named, spec.buttons))
        logger.info("%-9s %s -> %s", spec.short_name, report.summary(), path.name)
        if args.show_skipped:
            for skipped in report.skipped:
                logger.info("  skipped %s", skipped)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
