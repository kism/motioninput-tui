"""Last Blade 2, Washizuka Keiichiro. The one charge character worth the name.

The guide writes a charge as `b~f`, "hold the previous direction briefly", the
same notation the KoF guides use.
"""

from tests.engine.test_motions.harness import (
    BACK,
    DOWN,
    FORWARD,
    NEO_A,
    NEO_B,
    NEO_C,
    UP,
    Script,
    press,
    release,
)

CHARGE_BACK_FORWARD_SLASH: Script = [
    press(BACK, 0),
    press(FORWARD, 1000),
    release(BACK, 1005),
    press(NEO_A, 1040),
]

CHARGE_DOWN_UP_SLASH: Script = [
    press(DOWN, 0),
    press(UP, 1000),
    release(DOWN, 1005),
    press(NEO_B, 1040),
]

SHORT_BACK_FORWARD_SLASH: Script = [
    press(BACK, 0),
    press(FORWARD, 300),
    release(BACK, 305),
    press(NEO_A, 340),
]


def test_charge_back_forward_is_the_shikku_satsu(play) -> None:
    assert play(CHARGE_BACK_FORWARD_SLASH).moves == ["Shikku Satsu"]


def test_charge_down_up_is_the_koku_satsu(play) -> None:
    """Either slash does it, so the strong one lands the same move."""
    assert play(CHARGE_DOWN_UP_SLASH).moves == ["Koku Satsu"]


def test_a_brief_hold_is_not_a_charge(play) -> None:
    assert play(SHORT_BACK_FORWARD_SLASH).moves == []


def test_a_charge_move_can_open_a_chain(play) -> None:
    """Rouga is `b~f + C`, and the three moves the guide writes under it are
    ordinary quarter circles. Nothing about a chain cares that its parent was a
    charge: the parent coming out is the whole condition.
    """
    rouga = [press(BACK, 0), press(FORWARD, 1000), release(BACK, 1005), press(NEO_C, 1040)]
    clear = [release(FORWARD, 1100), release(NEO_C, 1100)]
    quarter_back = [press(DOWN, 1160), press(BACK, 1220), release(DOWN, 1260), press(NEO_C, 1300)]
    assert play([*rouga, *clear, *quarter_back]).moves == ["Rouga", "Shashiki"]


def test_the_same_quarter_circle_without_the_charge_move_is_not_the_link(play) -> None:
    """With no string open, `d, db, b + C` is not Shashiki - Washizuka has no
    plain move on it, so nothing comes out at all."""
    quarter_back = [press(DOWN, 0), press(BACK, 60), release(DOWN, 100), press(NEO_C, 140)]
    assert play(quarter_back).moves == []
