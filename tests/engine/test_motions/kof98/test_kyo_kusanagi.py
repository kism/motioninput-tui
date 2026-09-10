"""KoF '98, Kyo Kusanagi, on the Neo Geo's A B C D panel.

The same shared scripts as the Street Fighter games: a quarter circle is a
fireball, and the 3rd Strike "hold down, tap forward twice" shortcut gets a
dragon punch nowhere but 3rd Strike.
"""

from tests.engine.test_motions.harness import (
    DOWN,
    DOWN_DOUBLE_TAP_FORWARD_HP,
    FORWARD,
    HP,
    QUARTER_CIRCLE_FORWARD_HP,
    press,
    release,
)

# f, d, df + heavy punch: a clean dragon punch motion.
DRAGON_PUNCH_HP = [
    press(FORWARD, 0),
    release(FORWARD, 40),
    press(DOWN, 60),
    press(FORWARD, 110),
    press(HP, 150),
]


def test_quarter_circle_forward_is_dokugami(play) -> None:
    assert play(QUARTER_CIRCLE_FORWARD_HP).moves == ["115 Shiki Doku Kami"]


def test_hold_down_double_tap_forward_does_nothing(play) -> None:
    """KoF wants the real f,d,df, exactly as Alpha 3 and Super Turbo do."""
    assert play(DOWN_DOUBLE_TAP_FORWARD_HP).moves == []


def test_the_full_dragon_punch_motion_is_oniyaki(play) -> None:
    assert play(DRAGON_PUNCH_HP).moves == ["100 Shiki Oniyaki"]
