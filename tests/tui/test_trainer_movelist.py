"""ctrl+l steps the move list: beside the trainer, the whole screen, gone."""

import asyncio
from typing import TYPE_CHECKING

import pytest
from rich.text import Text
from textual.widgets import Static

from motioninput_tui.config import Config
from motioninput_tui.tui import MotionInputApp
from motioninput_tui.tui.screens.training import TrainingScreen
from motioninput_tui.tui.widgets.movelist import MoveList
from motioninput_tui.tui.widgets.panel import LIT, ButtonPads

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def config(tmp_path: Path) -> Config:
    """Ryu on the left-hand keyboard, written to a throwaway file."""
    return Config(game="sfiii3", character="ryu", layout="keyboard-left", path=tmp_path / "config.json")


def test_ctrl_l_cycles_beside_full_hidden(config: Config) -> None:
    async def session() -> list[tuple[bool, bool, bool]]:
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            trainer = app.screen
            assert isinstance(trainer, TrainingScreen)
            seen = []
            for _ in range(4):
                seen.append(
                    (
                        trainer.query_one(MoveList).display,
                        trainer.query_one("#left").display,
                        trainer.query_one("#pads").display,
                    )
                )
                await pilot.press("ctrl+l")
                await pilot.pause()
            return seen

    assert asyncio.run(session()) == [
        (True, True, False),  # beside the trainer
        (True, False, True),  # the whole screen, over the live panel
        (False, True, False),  # hidden
        (True, True, False),
    ]


def test_full_screen_gives_the_guides_words_unstruck_and_lights_the_panel(config: Config) -> None:
    async def session() -> tuple[Text, list[str]]:
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            trainer = app.screen
            assert isinstance(trainer, TrainingScreen)
            await pilot.press("ctrl+l")
            await pilot.press("j")  # LP
            await pilot.pause()
            body = trainer.query_one("#movelist-body", Static).content
            assert isinstance(body, Text)
            art = trainer.query_one(ButtonPads).art
            lit = [art.plain[span.start : span.end].strip("│╭╮╰╯─ ") for span in art.spans if span.style == LIT]
            return body, [label for label in lit if label]

    body, lit = asyncio.run(session())
    assert "↓ ↘ → + P" in body.plain  # Hadou Ken as the trainer writes it
    assert "qcf + P" in body.plain  # and as the guide does
    assert not any("strike" in str(span.style) for span in body.spans)
    assert "struck through" not in body.plain
    assert "LP" in lit
