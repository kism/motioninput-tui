"""Ultra SF4, Zangief. The 360 is lenient, and must not cross-fire with the DP."""

from tests.engine.test_motions.harness import BACK, DOWN, FORWARD, HP, LP, UP, press, release


def test_lenient_360_is_a_spinning_piledriver(play) -> None:
    """rotation_slack = 3, so f, d, b, u still counts as a full circle."""
    script = [
        press(FORWARD, 0),
        release(FORWARD, 40),
        press(DOWN, 80),
        release(DOWN, 120),
        press(BACK, 160),
        release(BACK, 200),
        press(UP, 240),
        press(LP, 260),
        release(UP, 300),
    ]
    assert play(script).moves == ["Spinning Piledriver"]


def test_dragon_punch_motion_is_banishing_flat_not_the_spd(play) -> None:
    """f, d, df + P is Zangief's Banishing Flat; the rotation must not steal it."""
    script = [
        press(FORWARD, 0),
        release(FORWARD, 40),
        press(DOWN, 70),
        press(FORWARD, 120),
        release(DOWN, 200),
        press(HP, 210),
        release(FORWARD, 240),
    ]
    assert play(script).moves == ["Banishing Flat"]
