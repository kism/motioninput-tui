"""Alpha 3, Akuma. Hyakki Shuu is a tiger knee: a quarter circle carried on to up-forward.

The guide writes it ``qcf,uf``, which used to come out as a motion of its own
rather than the tiger knee Super Turbo's Sagat has.
"""

from motioninput_tui.engine.motions import MotionKind
from tests.engine.test_motions.harness import DOWN, FORWARD, HK, HP, LP, UP, Script, press, release

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


# The dive opens three moves, and the guide names none of them: each is written
# as the dive's own command again with what to do next on the end, so the parent
# is found by matching that command rather than a name.


def test_a_punch_out_of_the_dive_is_the_gou_shou(play) -> None:
    assert play([*TIGER_KNEE_LP, press(HP, 400)]).moves == ["Hyakki Shuu", "Hyakki Gou Shou"]


def test_a_kick_out_of_the_dive_is_the_gou_sen(play) -> None:
    assert play([*TIGER_KNEE_LP, press(HK, 400)]).moves == ["Hyakki Shuu", "Hyakki Gou Sen"]


def test_doing_nothing_leaves_the_dive_alone(play) -> None:
    """`Hyakki Gou Zan` is the guide's name for the dive with no follow-up, so
    it is listed and linked but has no input of its own to recognise."""
    moves = {move.name: move for move in play([]).session.character.moves}
    assert moves["Hyakki Gou Zan"].follows == "Hyakki Shuu"
    assert not moves["Hyakki Gou Zan"].trainable


def test_a_punch_with_no_dive_open_is_not_the_gou_shou(play) -> None:
    assert play([press(HP, 0)]).moves == []
