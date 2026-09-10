"""Tab equips the next Super Art on the trainer, rather than moving focus.

The move list is a focusable ``VerticalScroll``, so the binding has to be a
priority one or Textual takes tab for itself. That is what these check.
"""

import asyncio
from typing import TYPE_CHECKING

import pytest

from motioninput_tui.config import Config
from motioninput_tui.tui import MotionInputApp
from motioninput_tui.tui.screens.training import TrainingScreen

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from pathlib import Path


@pytest.fixture
def config(tmp_path: Path) -> Config:
    """A 3rd Strike selection, so there are Super Arts to cycle."""
    return Config(game="sfiii3", character="sean", layout="keyboard-left", path=tmp_path / "config.json")


@pytest.fixture
def no_super_arts(tmp_path: Path) -> Config:
    """Super Turbo has no Super Arts, so tab should do nothing there."""
    return Config(game="hsf2", character="ryu", layout="keyboard-left", path=tmp_path / "config.json")


def run(coroutine: Callable[[], Awaitable[list[str]]]) -> list[str]:
    """Run one pilot session and hand back what it found."""
    return asyncio.run(coroutine())


def _cycle(config: Config, presses: int) -> Callable[[], Awaitable[list[str]]]:
    async def session() -> list[str]:
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test() as pilot:
            await pilot.pause()
            assert isinstance(app.screen, TrainingScreen)
            seen = [app.screen.session.super_art]
            for _ in range(presses):
                await pilot.press("tab")
                await pilot.pause()
                seen.append(app.screen.session.super_art)
            return seen

    return session


def test_tab_cycles_the_super_arts_and_wraps(config) -> None:
    assert run(_cycle(config, presses=3)) == ["I", "II", "III", "I"]


def test_tab_does_nothing_in_a_game_without_super_arts(no_super_arts) -> None:
    assert run(_cycle(no_super_arts, presses=2)) == ["", "", ""]
