"""KoF '98, Terry Bogard. Same shared scripts as the Street Fighter Ryu tests."""

from tests.engine.test_motions.harness import DOWN_DOUBLE_TAP_FORWARD_HP, QUARTER_CIRCLE_FORWARD_HP


def test_quarter_circle_forward_is_a_power_wave(play) -> None:
    assert play(QUARTER_CIRCLE_FORWARD_HP).moves == ["Power Wave"]


def test_hold_down_double_tap_forward_is_not_a_rising_tackle(play) -> None:
    """No dragon punch shortcut: down, forward, forward gets the df + C command
    normal, never the Rising Tackle that a real f,d,df would."""
    assert "Rising Tackle" not in play(DOWN_DOUBLE_TAP_FORWARD_HP).moves
