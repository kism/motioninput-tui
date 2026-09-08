"""KoF '98, Leona. A charge character: hold a direction, then strike the other way."""

from tests.engine.test_motions.harness import BACK, DOWN, FORWARD, HP, UP, press, release

# Hold down for well over the charge time, then up + punch.
CHARGE_DOWN_UP_HP = [
    press(DOWN, 0),
    press(UP, 1000),
    release(DOWN, 1005),
    press(HP, 1040),
]

# The same, charging back and releasing it forward.
CHARGE_BACK_FORWARD_HP = [
    press(BACK, 0),
    press(FORWARD, 1000),
    release(BACK, 1005),
    press(HP, 1040),
]

# Not held long enough to count as a charge.
SHORT_DOWN_UP_HP = [
    press(DOWN, 0),
    press(UP, 300),
    release(DOWN, 305),
    press(HP, 340),
]


def test_charge_down_up_is_a_moon_slasher(play) -> None:
    assert play(CHARGE_DOWN_UP_HP).moves == ["Moon Slasher"]


def test_charge_back_forward_is_a_baltic_launcher(play) -> None:
    assert play(CHARGE_BACK_FORWARD_HP).moves == ["Baltic Launcher"]


def test_a_brief_hold_is_not_a_charge(play) -> None:
    assert play(SHORT_DOWN_UP_HP).moves == []
