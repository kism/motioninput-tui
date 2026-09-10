"""The trainer runs on the gamepad layout even with no pad attached."""

import asyncio

from motioninput_tui.config import Config
from motioninput_tui.tui import MotionInputApp
from motioninput_tui.tui.screens.training import TrainingScreen


def test_gamepad_layout_starts_and_flags_the_missing_pad(tmp_path) -> None:
    async def session() -> str:
        config = Config(game="sfiii3", character="ryu", layout="gamepad", path=tmp_path / "config.json")
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.pause()
            assert isinstance(app.screen, TrainingScreen)
            return str(app.screen.query_one("#status").render())

    assert "no gamepad detected" in asyncio.run(session())
