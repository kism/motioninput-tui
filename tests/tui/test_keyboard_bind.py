"""Rebinding the custom keyboard layout from the input picker."""

import asyncio
from typing import TYPE_CHECKING

from textual.widgets import OptionList

from motioninput_tui.config import Config
from motioninput_tui.controls.layouts import KEYBOARD_SLOTS
from motioninput_tui.tui import MotionInputApp
from motioninput_tui.tui.screens.input_picker import InputPickerScreen
from motioninput_tui.tui.screens.keyboard_bind import KeyboardBindScreen

if TYPE_CHECKING:
    from pathlib import Path


def _open_rebind(app: MotionInputApp) -> InputPickerScreen:
    picker = app.screen
    assert isinstance(picker, InputPickerScreen)
    layouts = picker.query_one("#layouts", OptionList)
    layouts.highlighted = picker._custom_keyboard_index()
    return picker


def test_rebinding_a_key_persists_it(tmp_path: Path) -> None:
    config = Config(game="sfiii3", character="ryu", layout="keyboard-custom", path=tmp_path / "config.json")

    async def run() -> Config:
        app = MotionInputApp(config, key_release=False)
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.pause()
            _open_rebind(app)
            await pilot.pause()

            await pilot.press("b")
            await pilot.pause()
            bind = app.screen
            assert isinstance(bind, KeyboardBindScreen)
            bind.query_one("#binds", OptionList).highlighted = KEYBOARD_SLOTS.index("HP")
            await pilot.press("enter")  # arm HP
            await pilot.pause()
            assert bind._armed == "HP"
            await pilot.press(";")  # bind HP to semicolon
            await pilot.pause()
            assert bind._armed is None
            await pilot.press("escape")  # done
            await pilot.pause()
            await pilot.pause()
        return config

    result = asyncio.run(run())
    assert result.keyboard_bindings["HP"] == "semicolon"
    assert result.path is not None
    assert '"HP": "semicolon"' in result.path.read_text()


def test_binding_a_used_key_swaps_the_two() -> None:
    config = Config(layout="keyboard-custom")

    async def run() -> dict[str, str]:
        app = MotionInputApp(config, key_release=False)
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.pause()
            _open_rebind(app)
            await pilot.pause()
            await pilot.press("b")
            await pilot.pause()
            bind = app.screen
            assert isinstance(bind, KeyboardBindScreen)
            bind.query_one("#binds", OptionList).highlighted = KEYBOARD_SLOTS.index("LP")
            await pilot.press("enter")
            await pilot.press("k")  # k currently belongs to MP
            await pilot.pause()
            return dict(bind._keys)

    keys = asyncio.run(run())
    assert keys["LP"] == "k"
    assert keys["MP"] == "j"  # took LP's old key
