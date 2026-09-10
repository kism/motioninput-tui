"""The settings, from the setup screen's pane and from the trainer's modal.

Both are the same widget, so what matters is that a toggle survives the trip out
to the config file and back into the engine: at the start of a session from the
pane, and part way through one from the modal.
"""

import asyncio
from typing import TYPE_CHECKING

import pytest
from textual.widgets import OptionList

from motioninput_tui.config import Config
from motioninput_tui.engine.recognizer import BufferPolicy
from motioninput_tui.settings import SETTINGS
from motioninput_tui.tui import MotionInputApp
from motioninput_tui.tui.screens.settings import SettingsScreen
from motioninput_tui.tui.screens.setup import SetupScreen
from motioninput_tui.tui.screens.training import TrainingScreen
from motioninput_tui.tui.widgets.settings_list import SettingsList

if TYPE_CHECKING:
    from pathlib import Path

    from textual.pilot import Pilot


@pytest.fixture
def config(tmp_path: Path) -> Config:
    """A saved selection that writes back to a throwaway file, never the real one."""
    return Config(game="sfiii3", character="ken", layout="keyboard-left", path=tmp_path / "config.json")


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


def _row(attribute: str) -> int:
    """Where a setting sits in the pane, so inserting one cannot break a test."""
    return next(index for index, setting in enumerate(SETTINGS) if setting.attribute == attribute)


def test_toggling_a_setting_saves_it(config: Config) -> None:
    async def session() -> None:
        app = MotionInputApp(config, key_release=False)
        async with app.run_test() as pilot:
            setup = await _open_setup(pilot)
            settings = setup.query_one(SettingsList)
            assert settings.has_focus
            assert settings.highlighted == _row("lenient_half_circles") == 0
            await pilot.press("space")
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
            await pilot.press("space")  # relaxed half circles off
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
            settings = setup.query_one(SettingsList)
            return str(settings.get_option_at_index(0).prompt)

    assert asyncio.run(session()).startswith("[ ]")


def test_ctrl_b_opens_the_settings_over_the_trainer(config: Config) -> None:
    """The buffer hotkey now brings up every setting, not just that one."""

    async def session() -> str:
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("ctrl+b")
            await pilot.pause()
            await pilot.pause()
            return type(app.screen).__name__

    assert asyncio.run(session()) == "SettingsScreen"


def test_a_setting_toggled_over_the_trainer_applies_to_the_session(config: Config) -> None:
    """The session in progress takes the new rules, rather than the next one."""

    async def session() -> tuple[bool, bool]:
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test() as pilot:
            await pilot.pause()
            trainer = app.screen
            assert isinstance(trainer, TrainingScreen)
            before = trainer.session.ruleset.lenient_half_circles

            await pilot.press("ctrl+b")
            await pilot.pause()
            await pilot.pause()
            assert isinstance(app.screen, SettingsScreen)
            assert app.screen.query_one(SettingsList).highlighted == 0  # relaxed half circles
            await pilot.press("space")
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()
            await pilot.pause()
            return before, trainer.session.ruleset.lenient_half_circles

    before, after = asyncio.run(session())
    assert (before, after) == (True, False)
    assert config.lenient_half_circles is False


def test_the_buffer_rule_still_toggles_from_there(config: Config) -> None:
    """It was ctrl+b's only job before, so it has to still be reachable."""

    async def session() -> BufferPolicy:
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test() as pilot:
            await pilot.pause()
            trainer = app.screen
            assert isinstance(trainer, TrainingScreen)
            await pilot.press("ctrl+b")
            await pilot.pause()
            await pilot.pause()
            app.screen.query_one(SettingsList).highlighted = _row("loose_buffer")
            await pilot.pause()
            await pilot.press("space")
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()
            await pilot.pause()
            return trainer.session.policy

    assert asyncio.run(session()) is BufferPolicy.LOOSE
    assert config.buffer_policy is BufferPolicy.LOOSE


def test_enter_starts_training_rather_than_toggling(config: Config) -> None:
    """Space is the toggle now, so enter means on this pane what it does on the rest."""

    async def session() -> str:
        app = MotionInputApp(config, key_release=False)
        async with app.run_test() as pilot:
            setup = await _open_setup(pilot)
            assert setup.query_one(SettingsList).has_focus
            await pilot.press("enter")
            await pilot.pause()
            await pilot.pause()
            return type(app.screen).__name__

    assert asyncio.run(session()) == "TrainingScreen"
    assert config.lenient_half_circles is True  # left alone


def test_enter_closes_the_settings_modal(config: Config) -> None:
    """Nothing left for it to mean there, and it is what a person will press."""

    async def session() -> str:
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("ctrl+b")
            await pilot.pause()
            await pilot.pause()
            assert isinstance(app.screen, SettingsScreen)
            await pilot.press("enter")
            await pilot.pause()
            await pilot.pause()
            return type(app.screen).__name__

    assert asyncio.run(session()) == "TrainingScreen"
    assert config.lenient_half_circles is True  # not flipped on the way out
