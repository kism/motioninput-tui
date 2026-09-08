"""Main entrypoint."""

import argparse
import sys
from pathlib import Path

from rich import traceback

from .config import Config, config_path
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
        default=None,
        help=f"Control layout (default: last used, or {DEFAULT_LAYOUT}).",
    )
    parser.add_argument(
        "--no-key-release",
        action="store_true",
        help="Do not ask the terminal for key release reporting; infer holds from auto-repeat instead.",
    )
    parser.add_argument(
        "--loose-buffer",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Do not spend inputs when a move comes out, so one motion can feed several moves. "
        "Not how the games behave; it is also in the trainer's settings, ctrl+b. Default: last used.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help=f"Config file holding the last used selection (default: {config_path()}).",
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
            # The input display's "characters" are button sets, with no moves
            # to count, so they say what they are instead.
            if character.moves:
                logger.info("    %-22s %d trainable moves", character.key, len(character.trainable_moves))
            else:
                logger.info("    %-22s %s", character.key, character.name)
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

    config = Config.load(args.config)
    _apply_overrides(config, args)

    if not _resolve_selection(config, from_cli=bool(args.character)):
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

    from .tui import MotionInputApp  # ruff: ignore[import-outside-top-level] - importing textual is slow, only do it when running the app

    MotionInputApp(
        config,
        key_release=key_release,
        skip_setup=bool(args.game and args.character),
    ).run()
    return 0


def _resolve_selection(config: Config, *, from_cli: bool) -> bool:
    """Check the selection against the rosters. False means do not start.

    A remembered character can simply be gone: rosters are regenerated, and a
    name override in ``datagen/names.py`` renames the key with the character.
    That is no reason to refuse to start, so the selection is dropped and the
    picker opens on it instead. A character named on the command line is
    different, and still gets an error.
    """
    if not config.game:
        return True
    try:
        game = load_game(config.game)
    except GameDataMissingError as exc:
        logger.error("%s", exc)  # ruff: ignore[error-instead-of-exception] - a traceback helps nobody here
        return False
    if not config.character:
        return True
    try:
        config.character = game.character(config.character).key
    except KeyError as exc:
        if from_cli:
            logger.error("%s", exc)  # ruff: ignore[error-instead-of-exception] - a traceback helps nobody here
            return False
        logger.info("Forgetting the saved character, it is not in the roster any more: %s", exc)
        config.character = None
    return True


def _apply_overrides(config: Config, args: argparse.Namespace) -> None:
    """Let command line arguments win over what was remembered."""
    from .engine.recognizer import BufferPolicy  # ruff: ignore[import-outside-top-level] - keeps startup light

    if args.game:
        config.game = args.game
        # A game named without a character must not reuse the other game's one.
        config.character = args.character
    if args.character:
        config.character = args.character
    if args.layout:
        config.layout = args.layout
    if args.loose_buffer is not None:
        config.buffer_policy = BufferPolicy.LOOSE if args.loose_buffer else BufferPolicy.CONSUME


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
