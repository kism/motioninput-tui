"""Samurai Shodown II, Charlotte. Mashing a button that is not a punch.

`Slash rapidly` is this guide's way of writing a mash, and a slash is either of
the two buttons the panel puts where the Street Fighter games put punches.
"""

from tests.engine.test_motions.harness import DOWN, FORWARD, NEO_A, Script, press, release, taps

MASH_SLASH: Script = taps(NEO_A, 0, 5, gap_ms=90)

DRAGON_PUNCH_SLASH: Script = [
    press(FORWARD, 0),
    release(FORWARD, 50),
    press(DOWN, 90),
    press(FORWARD, 150),
    release(DOWN, 190),
    press(NEO_A, 200),
]


def test_mashing_a_slash_is_the_splash_fount(play) -> None:
    assert "Splash Fount" in play(MASH_SLASH).moves


def test_forward_down_downforward_with_a_slash_is_the_tri_slash(play) -> None:
    assert play(DRAGON_PUNCH_SLASH).moves == ["Tri-Slash"]
