"""Samurai Shodown II, Kuroko. A charge held in down-back, and a bare mash.

The guide writes the shuriken `db~f + A`: the charge is down-back itself, so
holding plain back for as long gives nothing. `C rapidly` is a mash with no
`+` in front of its button.
"""

from tests.engine.test_motions.harness import BACK, DOWN, FORWARD, NEO_A, NEO_C, Script, press, release, taps

DOWN_BACK_CHARGE_FORWARD_A: Script = [
    press(DOWN, 0),
    press(BACK, 0),
    release(BACK, 950),
    release(DOWN, 950),
    press(FORWARD, 970),
    press(NEO_A, 990),
]

BACK_CHARGE_FORWARD_A: Script = [
    press(BACK, 0),
    release(BACK, 950),
    press(FORWARD, 970),
    press(NEO_A, 990),
]

SHURIKEN = "Kuroko Hachigoku Tama Senbei Shuriken"


def test_down_back_charge_then_forward_is_the_shuriken(play) -> None:
    assert SHURIKEN in play(DOWN_BACK_CHARGE_FORWARD_A).moves


def test_a_plain_back_charge_is_not(play) -> None:
    assert SHURIKEN not in play(BACK_CHARGE_FORWARD_A).moves


def test_mashing_c_is_kuroko_gekira(play) -> None:
    assert "Kuroko Gekira" in play(taps(NEO_C, 0, 5, gap_ms=90)).moves
