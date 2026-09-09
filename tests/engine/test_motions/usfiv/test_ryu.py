"""Ultra SF4, Ryu. The shortcut game: both of 3rd Strike's dragon punch
shortcuts work, the diagonal one and the hold-down-double-tap.

Compare `sfiii3/test_ryu.py` (also a DP), and `sfa3/test_ryu.py` /
`hsf2/test_ryu.py` (nothing), which play the same canonical scripts.
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


def test_hold_down_double_tap_forward_is_a_dragon_punch(play) -> None:
    """SF4 takes the 3rd Strike shortcut: hold down, double tap forward, DP.

    This gives nothing in `hsf2` or `sfa3`.
    """
    assert "Shoryuken" in play(DOWN_DOUBLE_TAP_FORWARD_HP).moves


def test_crouching_double_tap_down_forward_is_a_dragon_punch(play) -> None:
    """Tapping df twice from a crouch, the notorious SF4 walk-up-DP: d, df, d, df, d + HP."""
    script = [
        press(DOWN, 0),
        press(FORWARD, 60),
        release(FORWARD, 110),
        press(FORWARD, 170),
        release(FORWARD, 220),
        press(HP, 260),
        release(HP, 300),
    ]
    assert play(script).moves == ["Shoryuken"]


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
