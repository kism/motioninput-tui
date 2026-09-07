"""Which picker the setup screen opens on.

Textual's test pilot is asynchronous, and the suite has no async plugin, so
each test drives one short session through ``asyncio.run``.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest
from textual.widgets import OptionList

from motioninput_tui.config import Config
from motioninput_tui.tui import MotionInputApp
from motioninput_tui.tui.screens.setup import SetupScreen

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from pathlib import Path


@pytest.fixture
def config(tmp_path: Path) -> Config:
    """A saved selection that writes back to a throwaway file, never the real one."""
    return Config(game="sfiii3", character="ken", layout="hitbox", path=tmp_path / "config.json")


def run(coroutine: Callable[[], Awaitable[str | None]]) -> str | None:
    """Run one pilot session and hand back what it found."""
    return asyncio.run(coroutine())


def test_leaving_the_trainer_focuses_the_character_list(config) -> None:
    """Escape out of the trainer is nearly always about picking someone else."""

    async def session() -> str | None:
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test() as pilot:
            await pilot.press("escape")
            await pilot.pause()
            await pilot.pause()
            assert isinstance(app.screen, SetupScreen)
            characters = app.screen.query_one("#characters", OptionList)
            assert characters.highlighted is not None
            assert str(characters.get_option_at_index(characters.highlighted).prompt) == "Ken"
            return app.focused.id if app.focused else None

    assert run(session) == "characters"


def test_launching_focuses_the_layout_list(config) -> None:
    """A cold start still begins at the top, where the layout is chosen."""

    async def session() -> str | None:
        app = MotionInputApp(config, key_release=False)
        async with app.run_test() as pilot:
            await pilot.pause()
            return app.focused.id if app.focused else None

    assert run(session) == "layouts"
