"""Sailor Moon S, Sailor Pluto. A half circle and a charge that both open on back."""

from tests.engine.test_motions.harness import (
    BACK,
    DOWN,
    FORWARD,
    SNES_HP,
    SNES_LK,
    SNES_LP,
    press,
    release,
)


def test_half_circle_forward_is_the_dead_scream(play) -> None:
    script = [
        press(BACK, 0),
        press(DOWN, 60),
        release(BACK, 100),
        press(FORWARD, 140),
        release(DOWN, 180),
        press(SNES_LP, 220),
    ]
    assert play(script).moves == ["Dead Scream"]


def test_a_half_circle_that_skips_the_down_gives_nothing(play) -> None:
    """The shape of `HALF_CIRCLE_SKIPPING_DOWN_MK`: back, add down, then swap
    back for forward in one go, so down-forward follows down-back and a plain
    down never appears. 3rd Strike reads a half circle at three points and takes
    it; this game has no such leniency, so the motion is simply incomplete."""
    script = [
        press(BACK, 0),
        press(DOWN, 60),
        release(BACK, 120),
        press(FORWARD, 120),
        release(DOWN, 180),
        press(SNES_LP, 220),
    ]
    assert play(script).moves == []


def test_charging_back_and_kicking_is_the_stork_sweep(play) -> None:
    """Both of her specials open on back, and only the pause tells them apart:
    this one never touches down, so the half circle above cannot claim it."""
    script = [press(BACK, 0), release(BACK, 2100), press(FORWARD, 2100), press(SNES_LK, 2150)]
    assert play(script).moves == ["Stork Sweep"]


def test_a_second_of_back_is_not_long_enough_to_charge(play) -> None:
    script = [press(BACK, 0), release(BACK, 1000), press(FORWARD, 1000), press(SNES_LK, 1050)]
    assert play(script).moves == []


def test_half_circle_back_then_forward_is_the_desperation(play) -> None:
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
    assert play(script).moves == ["Dimension Dance"]
