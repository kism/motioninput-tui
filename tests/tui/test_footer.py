"""Escape leads every footer, whatever else the screen or its focused list binds."""

import asyncio
from typing import TYPE_CHECKING

from motioninput_tui.config import Config
from motioninput_tui.tui import MotionInputApp

if TYPE_CHECKING:
    from pathlib import Path


def _first_shown(app: MotionInputApp) -> str:
    return next(key for key, active in app.screen.active_bindings.items() if active.binding.show)


def _config(tmp_path: Path) -> Config:
    return Config(game="sfiii3", character="ryu", layout="keyboard-left", path=tmp_path / "config.json")


def test_escape_comes_before_the_trainers_super_art_key(tmp_path: Path) -> None:
    async def session() -> str:
        app = MotionInputApp(_config(tmp_path), key_release=False, skip_setup=True)
        async with app.run_test() as pilot:
            await pilot.pause()
            return _first_shown(app)

    assert asyncio.run(session()) == "escape"


def test_escape_comes_before_the_focused_settings_list(tmp_path: Path) -> None:
    async def session() -> str:
        app = MotionInputApp(_config(tmp_path), key_release=False)
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.pause()
            await pilot.press("enter")  # past the input picker, onto the setup screen
            await pilot.pause()
            await pilot.pause()
            return _first_shown(app)

    assert asyncio.run(session()) == "escape"
