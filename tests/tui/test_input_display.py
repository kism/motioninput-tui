"""The input display: every roster's first character, drawn as the game's panel.

What matters is that every roster opens with it, that it knows every motion the
game has, that what is held is lit and what the stick made is drawn over the
history, and that rearranging the Neo Geo from the settings reaches a panel
already open.
"""

import asyncio
from typing import TYPE_CHECKING

import pytest
from rich.text import Text
from textual.widgets import OptionList, Static

from motioninput_tui.config import Config
from motioninput_tui.controls import gamepad
from motioninput_tui.engine.notation import ButtonRequirement
from motioninput_tui.engine.recognizer import NOT_MOTIONS
from motioninput_tui.games.loader import INPUT_DISPLAY, available_games, load_game
from motioninput_tui.notation_styles import DEFAULT
from motioninput_tui.settings import SETTINGS
from motioninput_tui.tui import MotionInputApp
from motioninput_tui.tui.screens.input_display import InputDisplayScreen
from motioninput_tui.tui.screens.settings import SettingsScreen
from motioninput_tui.tui.widgets.input_strip import InputStrip
from motioninput_tui.tui.widgets.panel import LIT, ButtonPads, DirectionGate
from motioninput_tui.tui.widgets.settings_list import SettingsList

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def config(tmp_path: Path) -> Config:
    """3rd Strike's input display on the southpaw layout, written to a throwaway file."""
    return Config(game="sfiii3", character=INPUT_DISPLAY, layout="keyboard-right", path=tmp_path / "config.json")


def _lit(art: Text) -> list[str]:
    """The labels inside the boxes that are lit up.

    A box is three or four lit lines, only some of which carry a label, so the
    borders come back blank and are dropped.
    """
    labels = (art.plain[span.start : span.end].strip("│╭╮╰╯─ ") for span in art.spans if span.style == LIT)
    return [label for label in labels if label]


def test_games_are_menu_ordered_by_series_then_number() -> None:
    """Series alphabetically, each in its own game order."""
    assert [game.key for game in available_games()] == [
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


def test_every_roster_opens_with_the_input_display() -> None:
    """It is the one you want without knowing who you want, so it comes first."""
    assert {game.characters[0].key for game in available_games()} == {INPUT_DISPLAY}


def test_the_input_display_knows_every_motion_in_the_game() -> None:
    """Whoever's move it is, and on any of the game's own buttons."""
    for game in available_games():
        display, *roster = game.characters
        motions = {move.motion.kind for character in roster for move in character.moves if move.motion is not None}
        assert {move.motion.kind for move in display.moves if move.motion is not None} == motions - NOT_MOTIONS
        any_button = ButtonRequirement(frozenset(game.buttons.buttons))
        assert all(move.motion is not None and move.motion.buttons == any_button for move in display.moves)


def test_every_motion_the_game_has_is_listed(config: Config) -> None:
    """Once each, air or not, in the notation the player picked."""

    async def session() -> list[str]:
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, InputDisplayScreen)
            return [str(label.content) for label in screen.query("#motions Static").results(Static)]

    display = load_game("sfiii3").character(INPUT_DISPLAY)
    kinds = {move.motion.kind for move in display.moves if move.motion is not None}
    assert sorted(asyncio.run(session())) == sorted(DEFAULT.write_kind(kind) for kind in kinds)


def test_the_motions_live_now_are_lit_in_the_list(config: Config) -> None:
    """Lit while a press would still bring one out, and out again once one has."""

    async def session() -> tuple[list[str], list[str]]:
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, InputDisplayScreen)

            def lit() -> list[str]:
                labels = screen.query("#motions Static").results(Static)
                return [
                    label.content.plain
                    for label in labels
                    if isinstance(label.content, Text) and label.content.style == LIT
                ]

            await pilot.press("k", "l")  # southpaw down, down-forward...
            screen.handle_release("k")  # ...forward
            await pilot.pause(0.05)
            live = lit()
            await pilot.press("a")  # LP brings it out
            await pilot.pause(0.05)
            return live, lit()

    live, spent = asyncio.run(session())
    assert "↓ ↘ →" in live
    assert "↓ ↘ →" not in spent


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


def test_what_the_stick_made_is_drawn_over_the_history(config: Config) -> None:
    """A quarter circle and a button: the motion over its inputs, green for the press that brought it out."""

    async def session() -> Text:
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test(size=(100, 26)) as pilot:
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, InputDisplayScreen)
            await pilot.press("k", "l")  # southpaw down, down-forward...
            screen.handle_release("k")  # ...forward
            await pilot.press("a")  # LP
            await pilot.pause(0.05)
            content = screen.query_one(InputStrip).content
            assert isinstance(content, Text)
            return content

    history = asyncio.run(session())
    drawn = [(history.plain[span.start : span.end], str(span.style)) for span in history.spans]
    assert any(text.startswith("↓ ↘ →") and style == "bold green" for text, style in drawn)


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
    config = Config(game="sfiii3", character=INPUT_DISPLAY, layout="gamepad", path=tmp_path / "config.json")

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


def test_the_panel_is_the_games_own_and_the_slant_setting_rearranges_it(tmp_path: Path) -> None:
    """The setting is global, so it has to reach a panel that is already up."""
    config = Config(game="kof98", character=INPUT_DISPLAY, layout="keyboard-right", path=tmp_path / "config.json")
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
    assert before["a"] == "A"  # the Neo Geo, straight across
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
            assert characters.option_count == len(load_game("sfiii3").characters)
            return type(app.screen).__name__

    assert asyncio.run(session()) == "SetupScreen"
