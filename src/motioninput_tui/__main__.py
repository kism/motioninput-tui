"""Main entrypoint."""

from __future__ import annotations

import argparse
import sys

from rich import traceback

from .constants import PROGRAM_NAME, PROGRAM_NAME_WITH_FULL_VERSION, PROGRAM_NAME_WITH_VERSION
from .controls.layouts import DEFAULT_LAYOUT, available_layouts
from .games.loader import GameDataMissingError, available_games, load_game
from .games.rulesets import GAME_SPECS
from .terminal import detect, query_support
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
    parser.add_argument(
        "--no-key-release",
        action="store_true",
        help="Do not ask the terminal for key release reporting; infer holds from auto-repeat instead.",
    )
    parser.add_argument(
        "--loose-buffer",
        action="store_true",
        help="Do not spend inputs when a move comes out, so one motion can feed several moves. "
        "Not how the games behave; toggle it in the trainer with ctrl+b.",
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

    releases = query_support()
    if releases is None:
        logger.info("Key releases: could not ask, no terminal attached.")
    elif releases:
        logger.info("Key releases: supported. Holds will be tracked exactly.")
    else:
        logger.warning(
            "Key releases: not supported. Holds will be inferred from auto-repeat, "
            "so charge moves depend on your keyboard repeat delay. "
            "Terminals that do support this: kitty, Ghostty, foot, WezTerm, Alacritty, Contour, Rio."
        )
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

    # Ask before the interface takes over the terminal, so holds are tracked
    # exactly from the very first keystroke rather than from the first release.
    key_release = False if args.no_key_release else bool(query_support())
    if key_release:
        logger.debug("Terminal reports key releases; holds will be tracked exactly")
    else:
        logger.info("Terminal does not report key releases; holds will be inferred from auto-repeat")

    from .engine.recognizer import BufferPolicy  # ruff: ignore[import-outside-top-level] - keeps startup light
    from .tui import MotionInputApp  # ruff: ignore[import-outside-top-level] - importing textual is slow, only do it when running the app

    MotionInputApp(
        game=args.game,
        character=args.character,
        layout=args.layout,
        key_release=key_release,
        policy=BufferPolicy.LOOSE if args.loose_buffer else BufferPolicy.CONSUME,
    ).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
