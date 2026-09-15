"""On the full-screen move list, ctrl+o picks a move and enter plays it back on the panel."""

import asyncio
from typing import TYPE_CHECKING

from textual.widgets import Static

from motioninput_tui.config import Config
from motioninput_tui.tui import MotionInputApp
from motioninput_tui.tui.screens.training import TrainingScreen
from motioninput_tui.tui.widgets.input_strip import InputStrip

if TYPE_CHECKING:
    from pathlib import Path


def test_enter_plays_the_picked_move_back_and_a_key_hands_the_panel_back(tmp_path: Path) -> None:
    config = Config(game="sfiii3", character="ryu", layout="keyboard-left", path=tmp_path / "config.json")

    async def session() -> tuple[bool, str, bool, str, str, bool, str]:
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            trainer = app.screen
            assert isinstance(trainer, TrainingScreen)
            await pilot.press("ctrl+l", "ctrl+l")  # full screen
            await pilot.press("down", "enter")  # not picking, so neither is picking's
            beside = trainer.playback is None and trainer.cursor is None
            await pilot.press("ctrl+o", "escape")  # escape stops picking rather than leaving
            assert app.screen is trainer
            assert not trainer.picking
            await pilot.press("ctrl+o")  # pick
            await pilot.press("down", "down", "down")  # past the three supers
            picked = trainer.cursor.name if trainer.cursor is not None else ""
            await pilot.press("enter")
            await pilot.pause(1.5)
            landed = trainer.playback is not None and trainer.playback.landed
            caption = str(trainer.query_one("#playback", Static).render())
            played = str(trainer.query_one("#strip", InputStrip).render())
            await pilot.press("d")  # forward: the player's again, and picking stops
            await pilot.pause()
            assert not trainer.picking
            await pilot.press("ctrl+o")  # back where it was
            assert trainer.cursor is not None
            assert trainer.cursor.name == "Hadou Ken"
            return (
                beside,
                picked,
                landed,
                caption,
                played,
                trainer.playback is None,
                str(trainer.query_one("#strip", InputStrip).render()),
            )

    beside, picked, landed, caption, played, handed_back, live = asyncio.run(session())
    assert beside
    assert picked == "Hadou Ken"
    assert landed
    assert caption.startswith("▶ Hadou Ken")
    assert "↓" in caption
    assert "LP" in caption
    assert "10f apart still land" in caption  # Third Strike's ten-frame step
    assert "↓ ↘ →" in played  # the motion laid over the inputs, as when the player does it
    assert handed_back
    assert "→" in live
    assert "LP" not in live
