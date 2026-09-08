"""Alpha 3, Ryu. Same inputs as `sfiii3/test_ryu.py`, stricter game."""

from tests.engine.test_motions.harness import DOWN_DOUBLE_TAP_FORWARD_HP, QUARTER_CIRCLE_FORWARD_HP


def test_quarter_circle_forward_is_a_fireball(play) -> None:
    assert play(QUARTER_CIRCLE_FORWARD_HP).moves == ["Hadou Ken"]


def test_hold_down_double_tap_forward_does_nothing(play) -> None:
    """Alpha 3 wants the down-forward, so the 3rd Strike shortcut gives nothing."""
    assert play(DOWN_DOUBLE_TAP_FORWARD_HP).moves == []
