"""The notation menu: picking a style rewrites the move list and is remembered.

The live input strip is checked here too, since the whole point of leaving it
out of the menu is that what you pressed always reads the same way.
"""

import asyncio
from typing import TYPE_CHECKING

import pytest
from textual.widgets import OptionList, Static

from motioninput_tui.config import Config
from motioninput_tui.tui import MotionInputApp
from motioninput_tui.tui.screens.notation import NotationScreen
from motioninput_tui.tui.screens.training import TrainingScreen
from motioninput_tui.tui.widgets.input_strip import InputStrip

if TYPE_CHECKING:
    from pathlib import Path

    from textual.pilot import Pilot


@pytest.fixture
def config(tmp_path: Path) -> Config:
    """A saved selection that writes back to a throwaway file, never the real one."""
    return Config(game="sfiii3", character="ryu", layout="hitbox", path=tmp_path / "config.json")


async def _pick(pilot: Pilot, family: int, style: int) -> None:
    """Open the menu and take one style, the way a player would."""
    await pilot.press("ctrl+n")
    await pilot.pause()
    await pilot.pause()
    screen = pilot.app.screen
    assert isinstance(screen, NotationScreen)
    screen.query_one("#families", OptionList).highlighted = family
    await pilot.pause()
    styles = screen.query_one("#styles", OptionList)
    styles.focus()
    styles.highlighted = style
    await pilot.pause()
    await pilot.press("enter")
    await pilot.pause()


def _movelist(screen: TrainingScreen) -> str:
    return str(screen.query_one("#movelist-body", Static).render())


def test_ctrl_n_opens_the_notation_menu(config: Config) -> None:
    async def session() -> str:
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("ctrl+n")
            await pilot.pause()
            await pilot.pause()
            return type(app.screen).__name__

    assert asyncio.run(session()) == "NotationScreen"


def test_picking_a_style_rewrites_the_move_list_and_is_saved(config: Config) -> None:
    """Dragon punches in kanji, without leaving the session."""

    async def session() -> tuple[str, str]:
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            trainer = app.screen
            assert isinstance(trainer, TrainingScreen)
            before = _movelist(trainer)
            await _pick(pilot, family=3, style=3)  # dragon punches, Dragon 龍
            await pilot.press("escape")
            await pilot.pause()
            await pilot.pause()
            return before, _movelist(trainer)

    before, after = asyncio.run(session())
    assert "→ ↓ ↘ + P" in before  # Shouryuu Ken, spelled out
    assert "龍 → + P" in after
    assert config.notation == {"dragon": "kanji"}
    assert config.path is not None
    assert '"dragon": "kanji"' in config.path.read_text()


def test_the_input_strip_stays_arrows_whatever_the_moves_are_written_in(config: Config) -> None:
    """Letters for the move list must not change what your own inputs look like."""

    async def session() -> tuple[str, str]:
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            trainer = app.screen
            assert isinstance(trainer, TrainingScreen)
            await _pick(pilot, family=0, style=1)  # directions, Letters
            await pilot.press("escape")
            await pilot.pause()
            for key in ("s", "d"):
                await pilot.press(key)
            await pilot.pause()
            return _movelist(trainer), str(trainer.query_one(InputStrip).render())

    movelist, strip = asyncio.run(session())
    assert "D, DF, F + P" in movelist
    assert "↓" in strip
    assert "D, DF" not in strip


def test_a_remembered_notation_is_used_from_the_start(tmp_path: Path) -> None:
    config = Config(
        game="sfiii3",
        character="ryu",
        layout="hitbox",
        notation={"quarter": "curved"},
        path=tmp_path / "config.json",
    )

    async def session() -> str:
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, TrainingScreen)
            return _movelist(screen)

    assert "⮩ + P" in asyncio.run(session())  # Hadou Ken
