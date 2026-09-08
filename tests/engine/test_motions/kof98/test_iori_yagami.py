"""KoF '98, Iori Yagami."""

from tests.engine.test_motions.harness import (
    DOWN,
    FORWARD,
    HP,
    QUARTER_CIRCLE_FORWARD_HP,
    press,
    release,
)

DRAGON_PUNCH_HP = [
    press(FORWARD, 0),
    release(FORWARD, 40),
    press(DOWN, 60),
    press(FORWARD, 110),
    press(HP, 150),
]


def test_quarter_circle_forward_is_yami_barai(play) -> None:
    assert play(QUARTER_CIRCLE_FORWARD_HP).moves == ["108 Shiki: Yami Barai"]


def test_the_dragon_punch_motion_is_oniyaki(play) -> None:
    assert play(DRAGON_PUNCH_HP).moves == ["100 Shiki: Oniyaki"]
