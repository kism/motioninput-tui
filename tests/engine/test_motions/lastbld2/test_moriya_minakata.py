"""Last Blade 2, Moriya Minakata. A dragon punch that wants the whole motion.

The two slashes are separate moves on the same input here, which is what the
`A or B` this guide writes everywhere does *not* mean: `f,d,df + A` and
`f,d,df + B` are the Shingetsu and its Ura.
"""

from tests.engine.test_motions.harness import (
    BACK,
    DOWN,
    DOWN_DOUBLE_TAP_FORWARD_HP,
    FORWARD,
    NEO_A,
    NEO_B,
    Script,
    press,
    release,
)

DRAGON_PUNCH_WEAK: Script = [
    press(FORWARD, 0),
    release(FORWARD, 50),
    press(DOWN, 90),
    press(FORWARD, 150),
    release(DOWN, 190),
    press(NEO_A, 200),
]

DRAGON_PUNCH_STRONG: Script = [*DRAGON_PUNCH_WEAK[:-1], press(NEO_B, 200)]

QUARTER_CIRCLE_BACK_STRONG: Script = [
    press(DOWN, 0),
    press(BACK, 70),
    release(DOWN, 110),
    press(NEO_B, 150),
]


def test_the_weak_slash_dragon_punch_is_the_shingetsu(play) -> None:
    assert play(DRAGON_PUNCH_WEAK).moves == ["Ittou Shingetsu"]


def test_the_strong_slash_dragon_punch_is_its_reverse(play) -> None:
    assert play(DRAGON_PUNCH_STRONG).moves == ["Ittou Shingetsu Ura"]


def test_hold_down_double_tap_forward_gives_nothing(play) -> None:
    """SNK has no dragon punch shortcut, as in KoF and Samurai Shodown."""
    assert play(DOWN_DOUBLE_TAP_FORWARD_HP).moves == []


def test_quarter_circle_back_with_the_strong_slash(play) -> None:
    assert play(QUARTER_CIRCLE_BACK_STRONG).moves == ["Ittou Oboro Chuudan"]


def test_the_strong_dragon_punch_out_of_the_weak_one_is_the_sogetsu(play) -> None:
    """The clearest case the mechanism has. `f,d,df + B` on its own is the
    Shingetsu Ura, asserted above; done straight out of the Shingetsu it is the
    Ittou Sogetsu instead, because the guide writes that one as a chain off it.
    """
    second = [
        release(FORWARD, 300),
        press(FORWARD, 340),
        release(FORWARD, 390),
        press(DOWN, 430),
        press(FORWARD, 490),
        release(DOWN, 530),
        press(NEO_B, 540),
    ]
    assert play([*DRAGON_PUNCH_WEAK, *second]).moves == ["Ittou Shingetsu", "Ittou Sogetsu"]
