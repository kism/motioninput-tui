"""ctrl+l steps the move list: beside the trainer, the whole screen, gone."""

import asyncio
from typing import TYPE_CHECKING

import pytest
from rich.text import Text
from textual.widgets import Static

from motioninput_tui.config import Config
from motioninput_tui.tui import MotionInputApp
from motioninput_tui.tui.screens.training import TrainingScreen
from motioninput_tui.tui.widgets.input_strip import InputStrip
from motioninput_tui.tui.widgets.movelist import LIT_ROW, MoveList
from motioninput_tui.tui.widgets.panel import LIT, ButtonPads, DirectionGate

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def config(tmp_path: Path) -> Config:
    """Ryu on the left-hand keyboard, written to a throwaway file."""
    return Config(game="sfiii3", character="ryu", layout="keyboard-left", path=tmp_path / "config.json")


def _lit(art: Text) -> list[str]:
    """The labels inside the panel's lit boxes, borders dropped."""
    labels = (art.plain[span.start : span.end].strip("│╭╮╰╯─ ") for span in art.spans if span.style == LIT)
    return [label for label in labels if label]


def _movelist(trainer: TrainingScreen) -> Text:
    body = trainer.query_one("#movelist-body", Static).content
    assert isinstance(body, Text)
    return body


def _lit_rows(trainer: TrainingScreen) -> list[str]:
    body = _movelist(trainer)
    return [body.plain[span.start : span.end] for span in body.spans if span.style == LIT_ROW]


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
    async def session() -> tuple[Text, list[str], list[str], str]:
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            trainer = app.screen
            assert isinstance(trainer, TrainingScreen)
            await pilot.press("ctrl+l")
            await pilot.press("d", "j")  # forward, LP
            await pilot.pause()
            return (
                _movelist(trainer),
                _lit(trainer.query_one(DirectionGate).art),
                _lit(trainer.query_one(ButtonPads).art),
                str(trainer.query_one("#pads InputStrip", InputStrip).render()),
            )

    body, stick, buttons, history = asyncio.run(session())
    assert "→LP" in history  # the history beside the panel, not just the hidden one
    assert "↓ ↘ → + P" in body.plain  # Hadou Ken as the trainer writes it
    assert "qcf + P" in body.plain  # and as the guide does
    assert not any("strike" in str(span.style) for span in body.spans)
    assert "struck through" not in body.plain
    assert stick == ["→"]
    assert "LP" in buttons


def test_the_panels_history_is_full_width_as_soon_as_it_is_shown(config: Config) -> None:
    """Hidden, it trims to nothing; shown, it must redraw without waiting for a key."""

    async def session() -> str:
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            trainer = app.screen
            assert isinstance(trainer, TrainingScreen)
            await pilot.press("s", "d", "j")  # down, down-forward + LP: wider than a hidden strip keeps
            # Let the holds lapse first, or their redraw would hide a missing one.
            await pilot.pause(trainer.session.hold_window_ms / 1000 + 0.1)
            await pilot.press("ctrl+l")
            await pilot.pause()
            await pilot.pause()
            return str(trainer.query_one("#pads InputStrip", InputStrip).render())

    assert "↓" in asyncio.run(session())


def test_the_panel_lays_the_motion_over_the_inputs_that_made_it(config: Config) -> None:
    async def session() -> str:
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            trainer = app.screen
            assert isinstance(trainer, TrainingScreen)
            await pilot.press("ctrl+l")
            await pilot.press("a")  # back, long enough ago to be no part of a motion,
            trainer.handle_release("a")  # so the quarter circle does not start the strip
            await pilot.pause(1)
            await pilot.press("s", "d")  # down, down-forward...
            trainer.handle_release("s")  # ...forward: a quarter circle
            await pilot.pause(0.05)  # a few ticks, which is what paints it
            return str(trainer.query_one("#panel-strip", InputStrip).render())

    *motions, inputs = asyncio.run(session()).split("\n")
    assert inputs.index("↓") > 0
    assert motions[-1].index("↓ ↘ →") == inputs.index("↓")


def test_motions_stay_drawn_ending_in_what_became_of_them(config: Config) -> None:
    """? on a quarter circle back left to lapse, ! on a quarter circle forward a Hadou Ken came out on."""

    async def session() -> str:
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            trainer = app.screen
            assert isinstance(trainer, TrainingScreen)
            await pilot.press("ctrl+l")
            await pilot.press("s", "a")
            trainer.handle_release("s")
            trainer.handle_release("a")
            await pilot.pause(1)  # long enough to lapse
            await pilot.press("s", "d")
            trainer.handle_release("s")
            await pilot.press("j")  # LP
            await pilot.pause(0.05)
            return str(trainer.query_one("#panel-strip", InputStrip).render())

    history = asyncio.run(session())
    assert "↓ ↙ ←?" in history
    assert "↓ ↘ →!" in history


def test_the_move_that_came_out_is_lit_then_goes_out(config: Config) -> None:
    async def session() -> tuple[str, list[str], list[str]]:
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            trainer = app.screen
            assert isinstance(trainer, TrainingScreen)
            await pilot.press("d", "k")  # forward + MP
            await pilot.pause()
            lit = _lit_rows(trainer)
            await pilot.pause(0.6)
            return trainer.session.activations[0].name, lit, _lit_rows(trainer)

    name, lit, later = asyncio.run(session())
    assert name == "Sakotsu Wari"
    assert len(lit) == 1
    assert "Sakotsu Wari" in lit[0]
    assert later == []
