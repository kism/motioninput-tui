"""The layout itself is checked, since the path is what selects the character.

A test filed under the wrong directory, or named after a character who is not
in that game's roster, would otherwise fail somewhere confusing.
"""

from pathlib import Path

import pytest

from motioninput_tui.games.loader import load_game
from motioninput_tui.games.rulesets import GAME_SPECS
from tests.engine.test_motions.harness import target_from_path

ROOT = Path(__file__).parent
GAME_DIRECTORIES = sorted(path for path in ROOT.iterdir() if path.is_dir() and not path.name.startswith((".", "__")))
CHARACTER_FILES = sorted(path for path in ROOT.glob("*/test_*.py"))


def test_there_are_game_directories() -> None:
    assert GAME_DIRECTORIES, "no games are covered"


@pytest.mark.parametrize("directory", GAME_DIRECTORIES, ids=lambda path: path.name)
def test_directory_is_a_known_game(directory: Path) -> None:
    assert directory.name in GAME_SPECS


@pytest.mark.parametrize("path", CHARACTER_FILES, ids=lambda path: f"{path.parent.name}/{path.stem}")
def test_file_is_a_character_in_that_game(path: Path) -> None:
    game_key, character_key = target_from_path(path.parts)
    assert load_game(game_key).character(character_key).key == character_key
