"""Martial Masters, Drunk Master. The half circle back that carries on to forward."""

from tests.engine.test_motions.harness import (
    BACK,
    DOWN,
    FORWARD,
    SNES_HK,
    SNES_HP,
    SNES_LK,
    SNES_LP,
    press,
    release,
)


def test_a_half_circle_back_ending_forward_is_the_butterfly_strike(play) -> None:
    """`hcb, f + P`. The last forward is a real second press, with back let go as
    it goes down: on the keyboard's neutral SOCD, forward on top of a held back
    would be neutral."""
    script = [
        press(FORWARD, 0),
        press(DOWN, 40),
        release(FORWARD, 80),
        press(BACK, 120),
        release(DOWN, 160),
        release(BACK, 200),
        press(FORWARD, 200),
        press(SNES_HP, 240),
    ]
    assert play(script).moves == ["Butterfly Strike"]


def test_stopping_at_back_gives_the_quarter_circle_instead(play) -> None:
    """The same roll without the forward on the end. Drunk Master has no plain
    `hcb + P`, and the tail of a half circle back is a quarter circle back, so
    what comes out is the Forward Roll - the cost of letting go a step early."""
    script = [
        press(FORWARD, 0),
        press(DOWN, 40),
        release(FORWARD, 80),
        press(BACK, 120),
        release(DOWN, 160),
        press(SNES_HP, 200),
    ]
    assert play(script).moves == ["Forward Roll"]


def test_a_half_circle_back_on_a_kick_is_the_sake_spit(play) -> None:
    script = [
        press(FORWARD, 0),
        press(DOWN, 40),
        release(FORWARD, 80),
        press(BACK, 120),
        release(DOWN, 160),
        press(SNES_LK, 200),
    ]
    assert play(script).moves == ["Sake Spit"]


def test_dragon_punch_is_the_gourd_swing(play) -> None:
    script = [
        press(FORWARD, 0),
        release(FORWARD, 60),
        press(DOWN, 60),
        press(FORWARD, 120),
        press(SNES_LP, 170),
    ]
    assert play(script).moves == ["Gourd Swing"]


def test_the_target_combo_is_a_run_of_presses_not_four_at_once(play) -> None:
    """The guide writes Drunken Combo `HP, HP, HK, HP`, one press after another.
    Read as four buttons together it would be a move the game does not have, so
    it is a sequence: three presses and then the one that fires it."""
    script = [
        press(SNES_HP, 0),
        release(SNES_HP, 40),
        press(SNES_HP, 200),
        release(SNES_HP, 240),
        press(SNES_HK, 400),
        release(SNES_HK, 440),
        press(SNES_HP, 600),
    ]
    assert play(script).moves[-1] == "Drunken Combo"


def test_the_last_press_of_the_combo_alone_is_nothing(play) -> None:
    """Which is the point of a sequence: the run in front of the press is what
    the move is, so the press on its own gives nothing."""
    assert play([press(SNES_HP, 0)]).moves == []
