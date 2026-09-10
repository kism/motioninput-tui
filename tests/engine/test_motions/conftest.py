"""Binds each test file to the game and character its path names."""

from typing import TYPE_CHECKING, Protocol

import pytest

from tests.engine.test_motions.harness import Attempt, Script, play_as, target_from_path

if TYPE_CHECKING:
    from pathlib import Path


class Play(Protocol):
    """Runs a script as the character the calling test file is named after."""

    def __call__(
        self, script: Script, *, exact_input: bool = True, super_art: str | None = None, settle_ms: int = 0
    ) -> Attempt:
        """Play the script and report what came out."""
        ...


class MisplacedTestError(Exception):
    """Raised when a motion test is not filed under a game directory."""

    def __init__(self, path: Path) -> None:
        """Say where the file should have gone."""
        super().__init__(f"{path} needs to live at test_motions/<game>/test_<character>.py to use the play fixture")


@pytest.fixture
def target(request: pytest.FixtureRequest) -> tuple[str, str]:
    """The (game, character) this test file stands for."""
    path = request.path
    if path.parent.name == "test_motions":
        raise MisplacedTestError(path)
    return target_from_path(path.parts)


@pytest.fixture
def play(target: tuple[str, str]) -> Play:
    """Run scripts against this file's character without naming them again."""
    game_key, character_key = target

    def _play(script: Script, *, exact_input: bool = True, super_art: str | None = None, settle_ms: int = 0) -> Attempt:
        return play_as(
            game_key, character_key, script, exact_input=exact_input, super_art=super_art, settle_ms=settle_ms
        )

    return _play
