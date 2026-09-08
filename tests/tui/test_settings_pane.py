"""The settings pane: toggling one saves it and the trainer starts with it.

The pane is the only way to reach the half circle rule, so what matters is that
a toggle survives the trip out to the config file and back into the engine.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest
from textual.widgets import OptionList

from motioninput_tui.config import Config
from motioninput_tui.tui import MotionInputApp
from motioninput_tui.tui.screens.setup import SetupScreen
from motioninput_tui.tui.screens.training import TrainingScreen

if TYPE_CHECKING:
    from pathlib import Path

    from textual.pilot import Pilot


@pytest.fixture
def config(tmp_path: Path) -> Config:
    """A saved selection that writes back to a throwaway file, never the real one."""
    return Config(game="sfiii3", character="ken", layout="hitbox", path=tmp_path / "config.json")


async def _open_setup(pilot: Pilot) -> SetupScreen:
    """Get past the input picker, onto the setup screen."""
    await pilot.pause()
    await pilot.pause()
    await pilot.press("enter")
    await pilot.pause()
    await pilot.pause()
    screen = pilot.app.screen
    assert isinstance(screen, SetupScreen)
    return screen


def test_toggling_a_setting_saves_it(config: Config) -> None:
    async def session() -> None:
        app = MotionInputApp(config, key_release=False)
        async with app.run_test() as pilot:
            setup = await _open_setup(pilot)
            settings = setup.query_one("#settings", OptionList)
            assert settings.has_focus
            assert settings.highlighted == 0  # relaxed half circles
            await pilot.press("enter")
            await pilot.pause()

    asyncio.run(session())
    assert config.lenient_half_circles is False
    assert config.path is not None
    assert '"lenient_half_circles": false' in config.path.read_text()


def test_the_trainer_starts_with_the_setting_applied(config: Config) -> None:
    """Turning the relaxation off has to reach the recogniser, not just the file."""

    async def session() -> bool:
        app = MotionInputApp(config, key_release=False)
        async with app.run_test() as pilot:
            setup = await _open_setup(pilot)
            await pilot.press("enter")  # relaxed half circles off
            await pilot.pause()
            setup.query_one("#characters", OptionList).focus()
            await pilot.pause()
            await pilot.press("enter")  # start training
            await pilot.pause()
            await pilot.pause()
            assert isinstance(app.screen, TrainingScreen)
            return app.screen.session.ruleset.lenient_half_circles

    assert asyncio.run(session()) is False


def test_a_saved_setting_comes_back_on(tmp_path: Path) -> None:
    """The pane opens on what was saved, so the toggle is not one way."""
    path = tmp_path / "config.json"
    Config(lenient_half_circles=False, path=path).save()
    reloaded = Config.load(path)

    async def session() -> str:
        app = MotionInputApp(reloaded, key_release=False)
        async with app.run_test() as pilot:
            setup = await _open_setup(pilot)
            settings = setup.query_one("#settings", OptionList)
            return str(settings.get_option_at_index(0).prompt)

    assert asyncio.run(session()).startswith("[ ]")
