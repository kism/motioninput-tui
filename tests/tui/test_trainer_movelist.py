"""ctrl+l steps the move list: beside the trainer, the whole screen, gone."""

import asyncio
from typing import TYPE_CHECKING

import pytest
from rich.text import Text
from textual.widgets import Static

from motioninput_tui.config import Config
from motioninput_tui.games.loader import load_game
from motioninput_tui.tui import MotionInputApp
from motioninput_tui.tui.screens.training import MOVELIST_MODES, TrainingScreen
from motioninput_tui.tui.widgets.input_strip import InputStrip
from motioninput_tui.tui.widgets.movelist import LIT_ROW, MIN_WIDTH, MoveList
from motioninput_tui.tui.widgets.panel import LIT, ButtonPads, DirectionGate, LivePanel
from motioninput_tui.tui.widgets.status_bar import StatusBar

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
                        trainer.query_one("#mash").display,
                    )
                )
                await pilot.press("ctrl+l")
                await pilot.pause()
            return seen

    assert asyncio.run(session()) == [
        (True, True, False),  # beside the trainer
        (True, False, True),  # the whole screen, the follow-through prompted under the history
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
                str(trainer.query_one("#strip", InputStrip).render()),
            )

    body, stick, buttons, history = asyncio.run(session())
    assert "→LP" in history  # the history under the panel
    assert "↓ ↘ → + P" in body.plain  # Hadou Ken as the trainer writes it
    assert "qcf + P" in body.plain  # and as the guide does
    assert not any("strike" in str(span.style) for span in body.spans)
    assert "struck through" not in body.plain
    assert stick == ["→"]
    assert "LP" in buttons


def test_the_live_panel_and_the_status_span_the_screen_whatever_the_move_list_is_doing(config: Config) -> None:
    """Beside, full screen or hidden, both stay along the bottom, as on the input display."""

    async def session() -> list[tuple[int, int]]:
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            trainer = app.screen
            assert isinstance(trainer, TrainingScreen)
            seen = []
            for _ in MOVELIST_MODES:
                # Inferred holds are worth a word, so the status has something to show.
                status = trainer.query_one(StatusBar)
                assert status.display
                seen.append((trainer.query_one(LivePanel).region.width, status.region.width))
                await pilot.press("ctrl+l")
                await pilot.pause()
            return seen

    assert asyncio.run(session()) == [(120, 120)] * len(MOVELIST_MODES)


def test_ctrl_p_hides_the_stick_and_the_buttons_and_gives_the_history_their_room(config: Config) -> None:
    async def session() -> list[tuple[bool, int]]:
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            trainer = app.screen
            assert isinstance(trainer, TrainingScreen)
            seen = []
            for _ in range(3):
                seen.append((trainer.query_one(DirectionGate).display, trainer.query_one("#strip").region.width))
                await pilot.press("ctrl+p")
                await pilot.pause()
            return seen

    (shown, beside), (hidden, alone), (back, beside_again) = asyncio.run(session())
    assert (shown, hidden, back) == (True, False, True)
    assert alone > beside == beside_again


def test_the_history_lays_the_motion_over_the_inputs_that_made_it(config: Config) -> None:
    async def session() -> str:
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            trainer = app.screen
            assert isinstance(trainer, TrainingScreen)
            await pilot.press("a")  # back, long enough ago to be no part of a motion,
            trainer.handle_release("a")  # so the quarter circle does not start the strip
            await pilot.pause(1)
            await pilot.press("s", "d")  # down, down-forward...
            trainer.handle_release("s")  # ...forward: a quarter circle
            await pilot.pause(0.05)  # a few ticks, which is what paints it
            return str(trainer.query_one("#strip", InputStrip).render())

    *motions, inputs = asyncio.run(session()).split("\n")
    assert inputs.index("↓") > 0
    assert motions[-1].index("↓ ↘ →") == inputs.index("↓")


def test_motions_stay_drawn_ending_in_what_became_of_them(config: Config) -> None:
    """Dim for a quarter circle back left to lapse, green for a quarter circle forward a Hadou Ken came out on."""

    async def session() -> Text:
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            trainer = app.screen
            assert isinstance(trainer, TrainingScreen)
            await pilot.press("s", "a")
            trainer.handle_release("s")
            trainer.handle_release("a")
            await pilot.pause(1)  # long enough to lapse
            await pilot.press("s", "d")
            trainer.handle_release("s")
            await pilot.press("j")  # LP
            await pilot.pause(0.05)
            content = trainer.query_one("#strip", InputStrip).content
            assert isinstance(content, Text)
            return content

    history = asyncio.run(session())
    drawn = [(history.plain[span.start : span.end], str(span.style)) for span in history.spans]
    assert any(text.startswith("↓ ↙ ←") and style == "dim" for text, style in drawn)
    assert any(text.startswith("↓ ↘ →") and style == "bold green" for text, style in drawn)


def test_a_move_with_no_motion_puts_a_green_mark_over_the_input_it_came_out_on(config: Config) -> None:
    """Sakotsu Wari, f + MP: no motion to draw, so the moment it came out is marked instead.

    A command normal rather than a throw, since the pilot's two keys land too
    far apart to be one press; `sfiii3/test_ryu.py` has the throw.
    """

    async def session() -> Text:
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            trainer = app.screen
            assert isinstance(trainer, TrainingScreen)
            await pilot.press("a")  # something first, so the mark is not at column 0
            trainer.handle_release("a")
            await pilot.pause(0.3)
            await pilot.press("d", "k")  # forward + MP
            trainer.handle_release("d")
            await pilot.pause(0.05)
            content = trainer.query_one("#strip", InputStrip).content
            assert isinstance(content, Text)
            return content

    history = asyncio.run(session())
    *motions, inputs = history.plain.split("\n")
    assert motions[-1].index("!") == inputs.index("MP") - 1  # over the direction glyph the button follows
    assert any(
        history.plain[span.start : span.end].startswith("!") and str(span.style) == "bold green"
        for span in history.spans
    )


def test_beside_the_trainer_the_move_list_grows_up_to_half_the_screen(tmp_path: Path) -> None:
    """Q's longest move name is cut to fit the narrowest list, and read whole once there is room."""
    config = Config(game="sfiii3", character="q", layout="keyboard-left", path=tmp_path / "config.json")
    longest = max((move.name for move in load_game("sfiii3").character("q").moves), key=len)

    async def session(width: int) -> tuple[int, str]:
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test(size=(width, 40)) as pilot:
            await pilot.pause()
            trainer = app.screen
            assert isinstance(trainer, TrainingScreen)
            return trainer.query_one(MoveList).region.width, _movelist(trainer).plain

    narrow_screen, wide_screen = 100, 200
    narrow_width, narrow = asyncio.run(session(narrow_screen))
    wide_width, wide = asyncio.run(session(wide_screen))
    assert narrow_width == MIN_WIDTH
    assert longest not in narrow
    assert MIN_WIDTH < wide_width <= wide_screen // 2
    assert longest in wide


def test_the_move_list_never_wraps_and_makes_room_for_the_guides_own_words(tmp_path: Path) -> None:
    """Alpha 3 Akuma's command grabs keep the guide's wording, longer than any input the trainer writes."""
    config = Config(game="sfa3", character="akuma", layout="keyboard-left", path=tmp_path / "config.json")
    wording = "Perform Gou Sai with K w/ foe in air"

    async def session(width: int) -> tuple[int, int, list[str]]:
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test(size=(width, 60)) as pilot:
            await pilot.pause()
            trainer = app.screen
            assert isinstance(trainer, TrainingScreen)
            body = trainer.query_one("#movelist-body", Static)
            drawn = ["".join(segment.text for segment in line) for line in body.render_lines(body.region.reset_offset)]
            return body.virtual_size.height, _movelist(trainer).plain.count("\n") + 1, drawn

    narrow_height, narrow_lines, _ = asyncio.run(session(100))
    wide_height, wide_lines, drawn = asyncio.run(session(300))
    assert narrow_height == narrow_lines  # cut short rather than wrapped
    assert wide_height == wide_lines
    assert any(wording in line for line in drawn)


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
