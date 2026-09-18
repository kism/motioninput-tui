"""Sailor Moon S, Sailor Venus. A half circle forward that turns back down."""

from tests.engine.test_motions.harness import (
    BACK,
    DOWN,
    FORWARD,
    SNES_HP,
    press,
    release,
)


def test_a_half_circle_forward_turned_back_down_is_the_wink_flare(play) -> None:
    """`b,db,d,df,f,df,d`, the mirror of Mars' Snake Flare. Her Crescent Beam is
    a plain quarter circle forward, which this completes on the way past and
    which is still live on this very press, so the longer motion has to win."""
    script = [
        press(BACK, 0),  # b
        press(DOWN, 45),  # db
        release(BACK, 90),  # d
        press(FORWARD, 135),  # df
        release(DOWN, 180),  # f
        press(DOWN, 225),  # df
        release(FORWARD, 270),  # d
        press(SNES_HP, 310),
    ]
    assert play(script).moves == ["Venus Wink Flare"]


def test_stopping_at_forward_is_the_crescent_beam(play) -> None:
    """The quarter circle on its own, on the same button."""
    script = [press(DOWN, 0), press(FORWARD, 70), release(DOWN, 110), press(SNES_HP, 150)]
    assert play(script).moves == ["Crescent Beam"]
