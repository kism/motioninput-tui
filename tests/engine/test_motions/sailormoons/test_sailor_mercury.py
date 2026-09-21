"""Sailor Moon S, Sailor Mercury. A tiger knee, a real dragon punch, and a charge."""

from tests.engine.test_motions.harness import (
    BACK,
    DOWN,
    FORWARD,
    SNES_HK,
    SNES_LK,
    SNES_LP,
    UP,
    press,
    release,
)


def test_quarter_circle_up_forward_is_the_aqua_mirage(play) -> None:
    """`d,df,f,uf`: the quarter circle carries on up rather than stopping at forward."""
    script = [
        press(DOWN, 0),
        press(FORWARD, 60),
        release(DOWN, 100),
        press(UP, 140),
        press(SNES_LP, 180),
    ]
    assert play(script).moves == ["Mercury Aqua Mirage"]


def test_forward_down_down_forward_is_the_reverse_break_step(play) -> None:
    """A genuine `f,d,df`, which is the only way this game gives a dragon punch."""
    script = [
        press(FORWARD, 0),
        release(FORWARD, 60),
        press(DOWN, 60),
        press(FORWARD, 120),
        press(SNES_LK, 160),
    ]
    assert play(script).moves == ["Reverse Break Step"]


def test_two_seconds_of_back_then_forward_is_the_shabon_spray(play) -> None:
    script = [press(BACK, 0), release(BACK, 2100), press(FORWARD, 2100), press(SNES_LP, 2150)]
    assert play(script).moves == ["Shabon Spray"]


def test_a_second_of_back_is_not_long_enough_to_charge(play) -> None:
    script = [press(BACK, 0), release(BACK, 1000), press(FORWARD, 1000), press(SNES_LP, 1050)]
    assert play(script).moves == []


def test_half_circle_back_then_forward_is_the_desperation(play) -> None:
    """`f,df,d,db,b,f`, the last forward a fresh press: back is let go as it goes
    down, since adding forward to back on a keyboard is neutral, not forward."""
    script = [
        press(FORWARD, 0),
        press(DOWN, 40),
        release(FORWARD, 80),
        press(BACK, 120),
        release(DOWN, 160),
        release(BACK, 200),
        press(FORWARD, 200),
        press(SNES_HK, 240),
    ]
    assert play(script).moves == ["Watery Bullet"]
