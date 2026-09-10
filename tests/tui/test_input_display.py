"""The input display: picked like a game, drawn as the panel it is.

What matters is that it stands up without a roster, that what is held is lit,
and that rearranging the Neo Geo from the settings reaches a panel already open.
"""

import asyncio
from typing import TYPE_CHECKING

import pytest
from textual.widgets import OptionList

from motioninput_tui.config import Config
from motioninput_tui.controls import buttons as sets
from motioninput_tui.controls import gamepad
from motioninput_tui.games.loader import available_games, load_game
from motioninput_tui.games.rulesets import DISPLAY_GAME
from motioninput_tui.settings import SETTINGS
from motioninput_tui.tui import MotionInputApp
from motioninput_tui.tui.screens.input_display import InputDisplayScreen
from motioninput_tui.tui.screens.settings import SettingsScreen
from motioninput_tui.tui.widgets.panel import LIT, ButtonPads, DirectionGate
from motioninput_tui.tui.widgets.settings_list import SettingsList

if TYPE_CHECKING:
    from pathlib import Path

    from rich.text import Text


@pytest.fixture
def config(tmp_path: Path) -> Config:
    """The display on the southpaw layout, written to a throwaway file."""
    return Config(
        game=DISPLAY_GAME,
        character=sets.STREET_FIGHTER.key,
        layout="keyboard-right",
        path=tmp_path / "config.json",
    )


def _lit(art: Text) -> list[str]:
    """The labels inside the boxes that are lit up.

    A box is three or four lit lines, only some of which carry a label, so the
    borders come back blank and are dropped.
    """
    labels = (art.plain[span.start : span.end].strip("│╭╮╰╯─ ") for span in art.spans if span.style == LIT)
    return [label for label in labels if label]


def test_the_display_is_the_first_game_offered() -> None:
    """It is the one you want without knowing what you want, so it comes first."""
    assert available_games()[0].key == DISPLAY_GAME


def test_games_are_menu_ordered_by_series_then_number() -> None:
    """Display first, then series alphabetically, each in its own game order."""
    assert [game.key for game in available_games()] == [
        DISPLAY_GAME,
        "kof98",
        "kof2001",
        "lb2",
        "ssii",
        "ssvsp",
        "hsf2",
        "sfa3",
        "sfiii3",
        "usfiv",
    ]


def test_its_characters_are_the_button_sets() -> None:
    """It has no roster; the panels stand in for one."""
    game = load_game(DISPLAY_GAME)
    assert [character.key for character in game.characters] == [entry.key for entry in sets.BUTTON_SETS]


def test_what_is_held_is_lit(config: Config) -> None:
    async def session() -> tuple[list[str], list[str]]:
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test(size=(100, 26)) as pilot:
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, InputDisplayScreen)
            await pilot.press("k")  # southpaw down
            await pilot.press("l")  # and forward, so down-forward
            await pilot.press("d")  # HP
            await pilot.pause()
            gate = screen.query_one(DirectionGate)
            pads = screen.query_one(ButtonPads)
            return _lit(gate.art), _lit(pads.art)

    directions, buttons = asyncio.run(session())
    assert directions == ["↘"]
    assert "HP" in buttons


def test_a_release_puts_a_button_out(config: Config) -> None:
    """Holds are drawn, so a button has to stop being held when it is let go."""

    async def session() -> list[str]:
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test(size=(100, 26)) as pilot:
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, InputDisplayScreen)
            await pilot.press("a")  # LP
            await pilot.pause()
            screen.handle_release("a")
            await pilot.pause()
            return _lit(screen.query_one(ButtonPads).art)

    assert asyncio.run(session()) == []


def test_a_held_pad_button_lights_the_panel(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The pad feeds the session, not `on_key`, so the panel has to read it back."""

    class MutablePad:
        name = "Fake Pad"

        def __init__(self) -> None:
            self.buttons: set[int] = set()
            self.axes: dict[int, float] = {}

        def get_button(self, button: int) -> int:
            return int(button in self.buttons)

        def get_axis(self, axis: int) -> float:
            return self.axes.get(axis, 0.0)

    pad = MutablePad()
    monkeypatch.setattr(gamepad, "_first_controller", lambda _pygame: pad)
    config = Config(
        game=DISPLAY_GAME, character=sets.STREET_FIGHTER.key, layout="gamepad", path=tmp_path / "config.json"
    )

    async def session() -> tuple[list[str], list[str]]:
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test(size=(100, 26)) as pilot:
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, InputDisplayScreen)
            if screen.session.gamepad is None:  # pragma: no cover - pygame missing
                pytest.skip("pygame is not available")
            pad.buttons = {gamepad._BUTTON_X}  # LP on the Xbox-style default
            await pilot.pause()
            held = _lit(screen.query_one(ButtonPads).art)
            pad.buttons = set()
            await pilot.pause()
            released = _lit(screen.query_one(ButtonPads).art)
            return held, released

    held, released = asyncio.run(session())
    assert "LP" in held
    assert released == []


def test_the_panel_is_the_one_the_character_names(tmp_path: Path) -> None:
    config = Config(
        game=DISPLAY_GAME, character=sets.TEKKEN.key, layout="keyboard-right", path=tmp_path / "config.json"
    )

    async def session() -> dict[str, str]:
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, InputDisplayScreen)
            return {key: button.value for key, button in screen.session.layout.attacks.items()}

    assert asyncio.run(session()) == {"a": "□", "s": "△", "z": "✕", "x": "○"}


def test_the_neo_geo_slant_setting_rearranges_an_open_panel(tmp_path: Path) -> None:
    """The setting is global, so it has to reach a panel that is already up."""
    config = Config(
        game=DISPLAY_GAME, character=sets.NEO_GEO.key, layout="keyboard-right", path=tmp_path / "config.json"
    )
    row = next(index for index, setting in enumerate(SETTINGS) if setting.attribute == "neo_geo_slant")

    async def session() -> tuple[dict[str, str], dict[str, str]]:
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, InputDisplayScreen)
            before = {key: button.value for key, button in screen.session.layout.attacks.items()}

            await pilot.press("ctrl+b")
            await pilot.pause()
            await pilot.pause()
            assert isinstance(app.screen, SettingsScreen)
            app.screen.query_one(SettingsList).highlighted = row
            await pilot.pause()
            await pilot.press("space")
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()
            await pilot.pause()
            after = {key: button.value for key, button in screen.session.layout.attacks.items()}
            return before, after

    before, after = asyncio.run(session())
    assert before["a"] == "A"  # straight across
    assert after == {"a": "C", "s": "D", "z": "A", "x": "B"}  # slanted
    assert config.neo_geo_slant is True


def test_leaving_the_display_goes_back_to_the_pickers(config: Config) -> None:
    async def session() -> str:
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()
            await pilot.pause()
            characters = app.screen.query_one("#characters", OptionList)
            assert characters.option_count == len(sets.BUTTON_SETS)
            return type(app.screen).__name__

    assert asyncio.run(session()) == "SetupScreen"
