"""KoF 2001, Terry. The double tap trap.

Terry's Rising Tackle is a down-charge, and holding down while tapping forward
looks superficially like the start of one. It must not come out: what the
double tap actually leaves held is down-forward, which is his `3+C` command
normal. Compare `kof98/test_terry_bogard.py`, the same trap a game earlier.
"""

from tests.engine.test_motions.harness import DOWN_DOUBLE_TAP_FORWARD_HP, QUARTER_CIRCLE_FORWARD_HP


def test_quarter_circle_forward_is_the_heavy_wave(play) -> None:
    assert play(QUARTER_CIRCLE_FORWARD_HP).moves == ["Round Wave"]


def test_the_double_tap_is_the_command_normal_not_a_charge(play) -> None:
    attempt = play(DOWN_DOUBLE_TAP_FORWARD_HP)

    assert attempt.moves == ["Rising Upper"]
    assert "Rising Tackle" not in attempt.moves
