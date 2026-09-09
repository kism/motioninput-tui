"""Ultra SF4, Ryu. The modern buffer: f,df is a dragon punch, but the 3rd
Strike hold-down-double-tap is not.

Compare `sfiii3/test_ryu.py`, `sfa3/test_ryu.py` and `hsf2/test_ryu.py`, which
play the same canonical scripts.
"""

from tests.engine.test_motions.harness import (
    DOWN,
    DOWN_DOUBLE_TAP_FORWARD_HP,
    FORWARD,
    HP,
    QUARTER_CIRCLE_FORWARD_HP,
    press,
    release,
)


def test_quarter_circle_forward_is_a_fireball(play) -> None:
    assert play(QUARTER_CIRCLE_FORWARD_HP).moves == ["Hadouken"]


def test_hold_down_double_tap_forward_does_nothing(play) -> None:
    """Unlike 3rd Strike, SF4 has no double-tap dragon punch shortcut."""
    assert play(DOWN_DOUBLE_TAP_FORWARD_HP).moves == []


def test_forward_then_down_forward_is_a_dragon_punch(play) -> None:
    """The SF4 shortcut: down skipped entirely, f, df alone gives a Shoryuken.

    This is why players eat an accidental DP walking up to throw, and it gives
    nothing in `hsf2` or `sfa3`.
    """
    script = [press(FORWARD, 0), press(DOWN, 60), press(HP, 110), release(HP, 150)]
    assert play(script).moves == ["Shoryuken"]


def test_clean_dragon_punch_motion(play) -> None:
    script = [
        press(FORWARD, 0),
        release(FORWARD, 40),
        press(DOWN, 70),
        press(FORWARD, 120),
        release(DOWN, 200),
        press(HP, 210),
        release(FORWARD, 240),
    ]
    assert play(script).moves == ["Shoryuken"]
