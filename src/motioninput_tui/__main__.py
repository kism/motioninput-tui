"""Main entrypoint."""

from __future__ import annotations

import argparse
import sys

from rich import traceback

from .constants import PROGRAM_NAME, PROGRAM_NAME_WITH_FULL_VERSION, PROGRAM_NAME_WITH_VERSION
from .controls.layouts import DEFAULT_LAYOUT, available_layouts
from .games.loader import GameDataMissingError, available_games, load_game
from .games.rulesets import GAME_SPECS
from .terminal import detect
from .utils.logger import get_logger, setup_logger_cli

traceback.install(extra_lines=2)
logger = get_logger(__name__)


def _get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog=PROGRAM_NAME, description="Fighting game motion input trainer.")
    parser.add_argument("--game", choices=sorted(GAME_SPECS), help="Skip the game picker.")
    parser.add_argument("--character", help="Skip the character picker. Needs --game.")
    parser.add_argument(
        "--layout",
        choices=sorted(layout.key for layout in available_layouts()),
        default=DEFAULT_LAYOUT,
        help=f"Control layout (default: {DEFAULT_LAYOUT}).",
    )
    parser.add_argument("--list", action="store_true", help="List games and characters, then exit.")
    parser.add_argument("--check-terminal", action="store_true", help="Report terminal suitability, then exit.")
    parser.add_argument("--version", action="version", version=PROGRAM_NAME_WITH_FULL_VERSION)
    parser.add_argument("-v", action="count", default=0, help="Increase verbosity (can be used multiple times).")
    return parser.parse_args()


def _print_terminal() -> int:
    info = detect()
    logger.info("Terminal: %s (%s, %s)", info.name, info.speed, info.detail)
    if info.warning():
        logger.warning("%s", info.warning())
    else:
        logger.info("Should be fast enough for accurate input timing.")
    return 0


def _print_roster() -> int:
    for game in available_games():
        logger.info("%s - %s", game.key, game.name)
        for character in game.characters:
            logger.info("    %-22s %d trainable moves", character.key, len(character.trainable_moves))
    return 0


def main() -> int:
    """Main entrypoint."""
    args = _get_args()
    setup_logger_cli(args.v)
    logger.debug("%s", PROGRAM_NAME_WITH_VERSION)

    if args.check_terminal:
        return _print_terminal()
    if args.list:
        return _print_roster()

    if args.character and not args.game:
        logger.error("--character needs --game as well")
        return 2

    try:
        if args.game:
            game = load_game(args.game)
            if args.character:
                game.character(args.character)
    except (GameDataMissingError, KeyError) as exc:
        logger.error("%s", exc)  # ruff: ignore[error-instead-of-exception] - a traceback helps nobody here
        return 1

    info = detect()
    if info.should_warn:
        logger.warning("%s", info.warning())

    from .tui import MotionInputApp  # ruff: ignore[import-outside-top-level] - importing textual is slow, only do it when running the app

    MotionInputApp(game=args.game, character=args.character, layout=args.layout).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
