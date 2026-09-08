"""Rebinding the gamepad attack buttons from the input picker."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest
from textual.widgets import OptionList

from motioninput_tui.config import Config
from motioninput_tui.controls import gamepad
from motioninput_tui.tui import MotionInputApp
from motioninput_tui.tui.screens.gamepad_bind import GamepadBindScreen
from motioninput_tui.tui.screens.input_picker import InputPickerScreen

if TYPE_CHECKING:
    from pathlib import Path


class FakeReader:
    """A pad that is always connected and presses whatever is queued."""

    def __init__(self) -> None:
        self.connected = True
        self.name = "Test Pad"
        self._queued: list[tuple[str, bool]] = []

    def press(self, code: str) -> None:
        self._queued.append((code, True))

    def poll(self, _at_ms: int) -> list[tuple[str, bool]]:
        events, self._queued = self._queued, []
        return events

    def reset(self) -> None: ...


@pytest.fixture
def fake_pad(monkeypatch: pytest.MonkeyPatch) -> FakeReader:
    reader = FakeReader()
    monkeypatch.setattr(gamepad, "GamepadReader", lambda: reader)
    return reader


def _gamepad_row(picker: InputPickerScreen) -> int:
    index = picker._gamepad_index()
    assert index is not None
    return index


def test_rebinding_an_attack_persists_it(tmp_path: Path, fake_pad: FakeReader) -> None:
    config = Config(game="sfiii3", character="ryu", layout="gamepad", path=tmp_path / "config.json")

    async def run() -> Config:
        app = MotionInputApp(config, key_release=False)
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.pause()
            picker = app.screen
            assert isinstance(picker, InputPickerScreen)
            layouts = picker.query_one("#layouts", OptionList)
            layouts.highlighted = _gamepad_row(picker)
            await pilot.pause()

            await pilot.press("b")
            await pilot.pause()
            await pilot.pause()
            bind = app.screen
            assert isinstance(bind, GamepadBindScreen)
            bind.query_one("#binds", OptionList).highlighted = 2  # HP
            await pilot.pause()
            await pilot.press("enter")  # arm HP
            await pilot.pause()
            assert bind._armed is not None
            fake_pad.press("pad:1")  # B on an Xbox pad
            bind._poll()  # what the poll interval does, but without the timing race
            await pilot.pause()
            await pilot.press("escape")  # done
            await pilot.pause()
            await pilot.pause()
        return config

    result = asyncio.run(run())
    assert result.gamepad_bindings["HP"] == "pad:1"
    assert result.path is not None
    assert '"HP": "pad:1"' in result.path.read_text()


@pytest.mark.usefixtures("fake_pad")
def test_rebind_hotkey_is_hidden_off_the_gamepad_row(tmp_path: Path) -> None:
    config = Config(game="sfiii3", character="ryu", layout="gamepad", path=tmp_path / "config.json")

    async def run() -> tuple[bool | None, bool | None]:
        app = MotionInputApp(config, key_release=False)
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.pause()
            picker = app.screen
            assert isinstance(picker, InputPickerScreen)
            layouts = picker.query_one("#layouts", OptionList)
            layouts.focus()
            layouts.highlighted = 0  # a keyboard layout
            await pilot.pause()
            off = picker.check_action("bind_gamepad", ())
            layouts.highlighted = _gamepad_row(picker)
            await pilot.pause()
            on = picker.check_action("bind_gamepad", ())
            return off, on

    off, on = asyncio.run(run())
    assert off is None
    assert on is True
