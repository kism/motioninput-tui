"""Samurai Shodown II, Wan Fu. The throw that asks for no direction at all.

Most of this guide's throws are written `b or f + button`, which says nothing
about which way to hold and so trains nothing. The two-button ones are the
exception: `b or f + AB` needs both slashes at once and no direction, which is
a motion the engine does have.
"""

from tests.engine.test_motions.harness import BACK, DOWN, NEO_A, NEO_B, Script, press, release

BOTH_SLASHES: Script = [press(NEO_A, 0), press(NEO_B, 8)]

QUARTER_CIRCLE_BACK_SLASH: Script = [
    press(DOWN, 0),
    press(BACK, 70),
    release(DOWN, 110),
    press(NEO_A, 150),
]


def test_both_slashes_with_no_direction_is_the_throw(play) -> None:
    assert play(BOTH_SLASHES).moves == ["Satsu Renha"]


def test_one_slash_alone_is_not(play) -> None:
    assert play([press(NEO_A, 0)]).moves == []


def test_quarter_circle_back_with_a_slash_is_the_fireball(play) -> None:
    assert play(QUARTER_CIRCLE_BACK_SLASH).moves == ["Kikou Bakutenhoh"]
