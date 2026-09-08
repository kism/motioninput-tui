"""3rd Strike, Ryu. The dragon punch shortcut lives here and nowhere else.

Compare `sfa3/test_ryu.py` and `hsf2/test_ryu.py`, which play the same script.
"""

from tests.engine.test_motions.harness import DOWN_DOUBLE_TAP_FORWARD_HP, QUARTER_CIRCLE_FORWARD_HP


def test_quarter_circle_forward_is_a_fireball(play) -> None:
    assert play(QUARTER_CIRCLE_FORWARD_HP).moves == ["Hadou Ken"]


def test_hold_down_double_tap_forward_is_a_dragon_punch(play) -> None:
    """3rd Strike accepts d, f, f as a shouryuuken. This is the headline difference."""
    assert "Shouryuu Ken" in play(DOWN_DOUBLE_TAP_FORWARD_HP).moves
