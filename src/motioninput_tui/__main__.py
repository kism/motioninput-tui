"""Main entrypoint."""

import argparse
import logging
import sys
from pathlib import Path

from rich import traceback

from .config import Config, config_path
from .constants import PROGRAM_NAME, PROGRAM_NAME_WITH_FULL_VERSION, PROGRAM_NAME_WITH_VERSION
from .games.loader import GameDataMissingError, available_games, load_game
from .terminal import detect, query_support
from .utils.logger import setup_logger_cli

traceback.install(extra_lines=2)
logger = logging.getLogger(__name__)


def _get_args() -> argparse.Namespace:
    """The whole command line.

    What to train is not here: the game, the character, the layout and the
    settings all live in the config file, which the pickers write as you use
    them. Duplicating them as flags meant two ways to say the same thing and a
    precedence rule between them. What is left either says *which* config file
    to read, or prints something and exits without one.
    """
    parser = argparse.ArgumentParser(prog=PROGRAM_NAME, description="Fighting game motion input trainer.")
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
            "Terminals that do support this: Ghostty, Alacritty, WezTerm, kitty, foot, Contour, Rio."
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

    config = Config.load(args.config)
    if not _resolve_selection(config):
        return 1

    info = detect()
    if info.should_warn:
        logger.warning("%s", info.warning())

    # Ask before the interface takes over the terminal, so holds are tracked
    # exactly from the very first keystroke rather than from the first release.
    key_release = bool(query_support())
    if key_release:
        logger.debug("Terminal reports key releases; holds will be tracked exactly")
    else:
        logger.info("Terminal does not report key releases; holds will be inferred from auto-repeat")

    from .tui import MotionInputApp  # ruff: ignore[import-outside-top-level] - importing textual is slow, only do it when running the app

    MotionInputApp(config, key_release=key_release).run()
    return 0


def _resolve_selection(config: Config) -> bool:
    """Check the remembered selection against the rosters. False means do not start.

    A remembered character can simply be gone: rosters are regenerated, and a
    name override in ``motioninput_tui_datagen/names.py`` renames the key with
    the character. That is no reason to refuse to start, so the selection is
    dropped and the picker opens on it instead. So is a game that is gone, as
    the input display is, which was a game before it was a character. Missing
    game *data* is a different matter, and there is nothing to fall back to.
    """
    if not config.game:
        return True
    try:
        game = load_game(config.game)
    except GameDataMissingError as exc:
        logger.error("%s", exc)  # ruff: ignore[error-instead-of-exception] - a traceback helps nobody here
        return False
    except KeyError as exc:
        logger.info("Forgetting the saved game, it is not one there is any more: %s", exc)
        config.game = config.character = None
        return True
    if not config.character:
        return True
    try:
        config.character = game.character(config.character).key
    except KeyError as exc:
        logger.info("Forgetting the saved character, it is not in the roster any more: %s", exc)
        config.character = None
    return True


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
