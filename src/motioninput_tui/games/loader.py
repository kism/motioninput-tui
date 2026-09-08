"""Loading rosters from the generated data files."""

import json
from functools import cache
from pathlib import Path

from motioninput_tui.controls.buttons import BUTTON_SETS
from motioninput_tui.utils.logger import get_logger

from .models import Character, Game
from .rulesets import DISPLAY_GAME, GAME_SPECS, GameSpec, get_spec

logger = get_logger(__name__)

DATA_DIR = Path(__file__).parent / "data"


class GameDataMissingError(FileNotFoundError):
    """Raised when a game's generated data file is not present."""

    def __init__(self, path: Path) -> None:
        """Point the user at the generator."""
        super().__init__(f"No roster data at {path}. Run: python -m motioninput_tui.datagen")


@cache
def load_game(key: str) -> Game:
    """Load a game and its roster. Cached, since the data never changes."""
    spec = get_spec(key)
    if spec.key == DISPLAY_GAME:
        return _display_game(spec)
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
        characters=characters,
        notes=spec.notes,
        source=spec.reference,
    )


def _display_game(spec: GameSpec) -> Game:
    """The input display, whose characters are the button sets.

    It has no roster to load, and nothing to recognise. Standing it up as a
    game is what lets it be picked with the same two lists as everything else,
    with the panel where the character goes.
    """
    characters = tuple(
        Character(key=button_set.key, name=button_set.name, title=button_set.note) for button_set in BUTTON_SETS
    )
    return Game(
        key=spec.key,
        name=spec.name,
        short_name=spec.short_name,
        ruleset=spec.ruleset,
        buttons=spec.buttons,
        characters=characters,
        notes=spec.notes,
    )


def available_games() -> list[Game]:
    """Every game that has roster data on disk."""
    games = []
    for key in GAME_SPECS:
        try:
            games.append(load_game(key))
        except GameDataMissingError:
            logger.warning("Skipping %s, no roster data generated yet", key)
    return games


def write_game(key: str, characters: list[Character]) -> Path:
    """Write a generated roster to the package data directory."""
    spec = get_spec(key)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / f"{spec.key}.json"
    payload = {
        "key": spec.key,
        "name": spec.name,
        "source": spec.reference,
        "characters": [character.to_dict() for character in characters],
    }
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=1, ensure_ascii=False)
        handle.write("\n")
    return path
