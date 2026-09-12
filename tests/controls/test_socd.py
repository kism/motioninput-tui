"""SOCD: a keyboard cancels opposites as GP2040-CE's neutral does, and nothing else does."""

from motioninput_tui.controls.layouts import HITBOX, gamepad_layout
from motioninput_tui.controls.source import KeyboardSource
from motioninput_tui.engine.notation import Direction
from tests.engine.test_motions.harness import BACK, DOWN, FORWARD, UP


def _held(source: KeyboardSource, *codes: str) -> Direction:
    for step, code in enumerate(codes):
        source.press(code, step * 10)
    return source.direction


def test_a_keyboard_cancels_left_and_right_so_left_down_right_is_down() -> None:
    assert _held(KeyboardSource(HITBOX, exact=True), BACK, DOWN, FORWARD) is Direction.DOWN


def test_a_keyboard_cancels_up_and_down_too() -> None:
    assert _held(KeyboardSource(HITBOX, exact=True), FORWARD, DOWN, UP) is Direction.FORWARD


def test_a_pad_is_not_cleaned_its_newer_input_wins() -> None:
    pad = KeyboardSource(gamepad_layout(None), exact=True)
    assert _held(pad, "pad:left", "pad:down", "pad:right") is Direction.DOWN_FORWARD


def test_inferred_holds_keep_the_newer_since_the_older_may_already_be_let_go() -> None:
    assert _held(KeyboardSource(HITBOX), BACK, DOWN, FORWARD) is Direction.DOWN_FORWARD
