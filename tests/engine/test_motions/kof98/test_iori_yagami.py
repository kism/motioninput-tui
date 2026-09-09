"""KoF '98, Iori Yagami."""

from tests.engine.test_motions.harness import (
    DOWN,
    FORWARD,
    HALF_CIRCLE_BACK_FORWARD_HP,
    HP,
    QUARTER_BACK_INTO_HALF_FORWARD_HP,
    QUARTER_CIRCLE_FORWARD_HP,
    QUARTER_FORWARD_INTO_HALF_BACK_HP,
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


def test_a_quarter_circle_rolled_into_a_half_circle_back_is_ya_otome(play) -> None:
    """`qcf,hcb + P`, with the forward the two halves meet on pressed once."""
    assert play(QUARTER_FORWARD_INTO_HALF_BACK_HP).moves == ["Kin 1211 Shiki: Ya Otome"]


def test_the_mirrored_roll_is_ya_sakazuki(play) -> None:
    """`qcb,hcf + P`, sharing the back instead."""
    assert play(QUARTER_BACK_INTO_HALF_FORWARD_HP).moves == ["Ura 108 Shiki: Ya Sakazuki"]


def test_a_half_circle_back_into_forward_is_kuzukaze(play) -> None:
    """`hcb,f + P`. Here the last forward *is* a second press, unlike the rolls
    above: the half circle ends on back and the command asks for forward next."""
    assert play(HALF_CIRCLE_BACK_FORWARD_HP).moves == ["Kuzukaze"]
