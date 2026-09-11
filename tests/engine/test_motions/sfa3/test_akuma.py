"""Alpha 3, Akuma. Hyakki Shuu is a tiger knee: a quarter circle carried on to up-forward.

The guide writes it ``qcf,uf``, which used to come out as a motion of its own
rather than the tiger knee Super Turbo's Sagat has.
"""

from motioninput_tui.engine.motions import MotionKind
from tests.engine.test_motions.harness import DOWN, FORWARD, LP, UP, Script, press, release

TIGER_KNEE_LP: Script = [
    press(DOWN, 0),
    press(FORWARD, 50),  # down-forward
    release(DOWN, 100),  # forward
    press(UP, 150),  # up-forward
    press(LP, 180),
]


def test_hyakki_shuu_comes_out_of_a_tiger_knee(play) -> None:
    assert play(TIGER_KNEE_LP).moves == ["Hyakki Shuu"]


def test_the_motion_is_read_as_a_tiger_knee(play) -> None:
    kinds = [motion.kind for motion in play(TIGER_KNEE_LP).session.trail]
    assert MotionKind.TIGER_KNEE in kinds
