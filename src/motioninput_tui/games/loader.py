"""Loading rosters from the generated data files."""

import json
import logging
from dataclasses import replace
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING

from motioninput_tui.engine.notation import ButtonRequirement
from motioninput_tui.engine.recognizer import NOT_MOTIONS

from .models import Category, Character, Game, Move
from .rulesets import GAME_SPECS, get_spec

if TYPE_CHECKING:
    from collections.abc import Iterable

    from motioninput_tui.controls.buttons import ButtonSet

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent / "data"

INPUT_DISPLAY = "input-display"
"""The key of the character every roster opens with: the input display."""


class GameDataMissingError(FileNotFoundError):
    """Raised when a game's generated data file is not present."""

    def __init__(self, path: Path) -> None:
        """Point the user at the generator."""
        super().__init__(f"No roster data at {path}. Run: python -m motioninput_tui_datagen")


@cache
def load_game(key: str) -> Game:
    """Load a game and its roster, the input display first. Cached, since the data never changes."""
    spec = get_spec(key)
    path = DATA_DIR / f"{spec.key}.json"
    if not path.is_file():
        raise GameDataMissingError(path)

    with path.open(encoding="utf-8") as handle:
        raw = json.load(handle)

    characters = tuple(Character.from_dict(entry) for entry in raw.get("characters", []))
    logger.debug("Loaded %s: %d characters", spec.short_name, len(characters))
    return Game(
        key=spec.key,
        name=spec.name,
        short_name=spec.short_name,
        ruleset=spec.ruleset,
        buttons=spec.buttons,
        characters=(_input_display(characters, spec.buttons), *characters),
        notes=spec.notes,
        source=spec.reference,
    )


def _input_display(roster: Iterable[Character], buttons: ButtonSet) -> Character:
    """The input display, as a character whose moves are every motion in the roster.

    Each is taken on any of the game's buttons and without its follow-through,
    so a press on whatever the stick has made brings it out: the display shows
    the motions, not whose move they are. Throws, holds and mashes are not
    motions, and are left out.
    """
    any_button = ButtonRequirement(frozenset(buttons.buttons))
    motions = dict.fromkeys(
        replace(move.motion, buttons=any_button, mash=0, mash_rhythm=False, mash_button="", notation="")
        for character in roster
        for move in character.moves
        if move.motion is not None and move.motion.kind not in NOT_MOTIONS
    )
    moves = tuple(
        Move(
            # Named for the air as well, since the recogniser tells moves apart by name.
            name=f"{spec.kind.value}{' air' if spec.air else ''}",
            command=spec.kind.value,
            category=Category.SPECIAL,
            motion=spec,
        )
        for spec in motions
    )
    return Character(key=INPUT_DISPLAY, name="Input display", title="every motion in the game", moves=moves)


def available_games() -> list[Game]:
    """Every game that has roster data on disk."""
    games = []
    for key in GAME_SPECS:
        try:
            games.append(load_game(key))
        except GameDataMissingError:
            logger.warning("Skipping %s, no roster data generated yet", key)
        except OSError, ValueError, KeyError, TypeError:
            # Unreadable or malformed data is one game missing from the picker,
            # not a reason to refuse to start. JSONDecodeError is a ValueError.
            logger.warning("Skipping %s, its roster data could not be read", key, exc_info=True)
    return games
