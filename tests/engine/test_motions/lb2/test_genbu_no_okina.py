"""Last Blade 2, Genbu no Okina. Three moves on one reverse dragon punch.

`b,d,db` is rare in the Street Fighter rosters and Okina has it on all three
attack buttons, so the button decides the move and nothing else does.
"""

from tests.engine.test_motions.harness import BACK, DOWN, NEO_A, NEO_B, NEO_C, Script, press, release

REVERSE_DRAGON_PUNCH: Script = [
    press(BACK, 0),
    release(BACK, 50),
    press(DOWN, 90),
    press(BACK, 150),
    release(DOWN, 190),
]


def _with(key: str) -> Script:
    return [*REVERSE_DRAGON_PUNCH, press(key, 200)]


def test_the_weak_slash_is_the_mukuyu_jin(play) -> None:
    assert play(_with(NEO_A)).moves == ["Mukuyu Jin"]


def test_the_strong_slash_is_the_mukuyu_chi(play) -> None:
    assert play(_with(NEO_B)).moves == ["Mukuyu Chi"]


def test_the_kick_is_the_mukuyu_ten(play) -> None:
    assert play(_with(NEO_C)).moves == ["Mukuyu Ten"]
