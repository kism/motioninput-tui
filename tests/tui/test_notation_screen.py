"""The notation, in the settings menu: picking a style rewrites the move list and is remembered.

The live input strip is checked here too, since the whole point of leaving it
out of the menu is that what you pressed always reads the same way.
"""

import asyncio
from typing import TYPE_CHECKING

import pytest
from textual.widgets import OptionList, Static

from motioninput_tui.config import Config
from motioninput_tui.notation_styles import FAMILY_NAMES, STYLES, Family
from motioninput_tui.tui import MotionInputApp
from motioninput_tui.tui.screens.settings import SettingsScreen
from motioninput_tui.tui.screens.training import TrainingScreen
from motioninput_tui.tui.widgets.input_strip import InputStrip

if TYPE_CHECKING:
    from pathlib import Path

    from textual.pilot import Pilot


@pytest.fixture
def config(tmp_path: Path) -> Config:
    """A saved selection that writes back to a throwaway file, never the real one."""
    return Config(game="sfiii3", character="ryu", layout="keyboard-left", path=tmp_path / "config.json")


async def _pick(pilot: Pilot, family: Family, style: int) -> None:
    """Open the menu and take one style, the way a player would."""
    await pilot.press("ctrl+b")
    await pilot.pause()
    await pilot.pause()
    screen = pilot.app.screen
    assert isinstance(screen, SettingsScreen)
    # Looked up rather than counted, so a family added to the menu cannot move it.
    # The first section is the toggles.
    screen.query_one("#sections", OptionList).highlighted = list(FAMILY_NAMES).index(family) + 1
    await pilot.pause()
    styles = screen.query_one("#styles", OptionList)
    styles.focus()
    styles.highlighted = style
    await pilot.pause()
    await pilot.press("space")
    await pilot.pause()


def _movelist(screen: TrainingScreen) -> str:
    return str(screen.query_one("#movelist-body", Static).render())


def test_the_notation_is_a_section_of_the_settings_menu(config: Config) -> None:
    """Left out to the sections, down to directions, right into its styles, and space takes one."""

    async def session() -> None:
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test() as pilot:
            await pilot.pause()
            for key in ("ctrl+b", "left", "down", "right", "down", "space"):
                await pilot.press(key)
                await pilot.pause()
                await pilot.pause()

    asyncio.run(session())
    assert config.notation == {"directions": "letters"}


def test_picking_a_style_rewrites_the_move_list_and_is_saved(config: Config) -> None:
    """Dragon punches in kanji, without leaving the session."""

    async def session() -> tuple[str, str]:
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            trainer = app.screen
            assert isinstance(trainer, TrainingScreen)
            before = _movelist(trainer)
            kanji = [style.key for style in STYLES[Family.DRAGON]].index("kanji")
            await _pick(pilot, family=Family.DRAGON, style=kanji)  # Dragon 龍
            await pilot.press("enter")  # done
            await pilot.pause()
            await pilot.pause()
            assert app.screen is trainer
            return before, _movelist(trainer)

    before, after = asyncio.run(session())
    assert "→ ↓ ↘ + P" in before  # Shouryuu Ken, spelled out
    assert "龍→ + P" in after
    assert config.notation == {"dragon": "kanji"}
    assert config.path is not None
    assert '"dragon": "kanji"' in config.path.read_text()


def test_the_input_strip_stays_arrows_whatever_the_moves_are_written_in(config: Config) -> None:
    """Letters for the move list, and for the motion rows over the history, must not change what your own inputs
    look like."""

    async def session() -> tuple[str, str]:
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            trainer = app.screen
            assert isinstance(trainer, TrainingScreen)
            await _pick(pilot, family=Family.DIRECTIONS, style=1)  # Letters
            await pilot.press("escape")
            await pilot.pause()
            for key in ("s", "d"):
                await pilot.press(key)
            await pilot.pause()
            # The last line is the inputs; any motion rows over them follow the notation.
            return _movelist(trainer), str(trainer.query_one("#strip", InputStrip).render()).split("\n")[-1]

    movelist, inputs = asyncio.run(session())
    assert "D, DF, F + P" in movelist
    assert "↓" in inputs
    assert "D, DF" not in inputs


def test_a_remembered_notation_is_used_from_the_start(tmp_path: Path) -> None:
    config = Config(
        game="sfiii3",
        character="ryu",
        layout="keyboard-left",
        notation={"quarter": "elbow"},
        path=tmp_path / "config.json",
    )

    async def session() -> str:
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, TrainingScreen)
            return _movelist(screen)

    assert "⬏ + P" in asyncio.run(session())  # Hadou Ken
