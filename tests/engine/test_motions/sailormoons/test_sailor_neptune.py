"""Sailor Moon S, Sailor Neptune. The dragon punch, and the dragon punch twice."""

from tests.engine.test_motions.harness import (
    DOWN,
    FORWARD,
    SNES_HP,
    press,
    release,
)


def test_two_dragon_punches_are_the_dragon_rise(play) -> None:
    """`f,d,df,f,d,df`. The second half is a whole dragon punch in its own right,
    finishing just before the button, so her Splash Edge is live on exactly this
    press: the doubled motion has to outrank it."""
    script = [
        press(FORWARD, 0),  # f
        release(FORWARD, 45),
        press(DOWN, 45),  # d
        press(FORWARD, 90),  # df
        release(DOWN, 135),  # f
        release(FORWARD, 180),
        press(DOWN, 180),  # d
        press(FORWARD, 225),  # df
        press(SNES_HP, 265),
    ]
    assert play(script).moves == ["Dragon Rise"]


def test_one_dragon_punch_is_the_splash_edge(play) -> None:
    """The same input stopped halfway, on the same button."""
    script = [
        press(FORWARD, 0),
        release(FORWARD, 45),
        press(DOWN, 45),
        press(FORWARD, 90),
        press(SNES_HP, 130),
    ]
    assert play(script).moves == ["Splash Edge"]
