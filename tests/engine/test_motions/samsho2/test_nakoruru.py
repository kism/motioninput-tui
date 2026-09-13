"""Samurai Shodown II, Nakoruru. A quarter circle that ends on down.

`b, db, d + Slash` rolls from back down onto down and stops there, the other
way round from a quarter circle back.
"""

from tests.engine.test_motions.harness import BACK, DOWN, NEO_A, Script, press, release

BACK_TO_DOWN_SLASH: Script = [
    press(BACK, 0),
    press(DOWN, 60),
    release(BACK, 100),
    press(NEO_A, 140),
]


def test_back_rolled_onto_down_with_a_slash_is_annu_mutsube(play) -> None:
    assert play(BACK_TO_DOWN_SLASH).moves == ["Annu Mutsube"]
