"""3rd Strike, Sean. All three of his Super Arts are ``qcf,qcf + P``.

You equip one before a match, so the trainer does too: only the selected Super
Art can come out, which is the only thing that tells Hadou Burst (SA I),
Shouryuu Cannon (SA II) and Hyper Tornado (SA III) apart. Shouryuu Cannon is
also the one with a "tap P rapidly" tail, so on SA II the motion alone is not
enough.
"""

from tests.engine.test_motions.harness import DOWN, FORWARD, HP, Script, press, release


def _quarter_circle(at: int) -> Script:
    return [press(DOWN, at), press(FORWARD, at + 50), release(DOWN, at + 90), release(FORWARD, at + 130)]


TWO_QUARTER_CIRCLES: Script = [*_quarter_circle(0), *_quarter_circle(160)]

DOUBLE_QCF_NO_MASH: Script = [*TWO_QUARTER_CIRCLES, press(HP, 340)]

DOUBLE_QCF_THEN_MASH: Script = [
    *TWO_QUARTER_CIRCLES,
    press(HP, 340),
    release(HP, 370),
    press(HP, 400),
    release(HP, 430),
    press(HP, 460),
]


def test_the_first_super_art_is_equipped_to_start_with(play) -> None:
    assert play(DOUBLE_QCF_NO_MASH).moves == ["Hadou Burst"]


def test_each_super_art_answers_the_same_motion_differently(play) -> None:
    """The same input, three answers: this is the whole point of selecting one."""
    assert play(DOUBLE_QCF_NO_MASH, super_art="I").moves == ["Hadou Burst"]
    assert play(DOUBLE_QCF_NO_MASH, super_art="III").moves == ["Hyper Tornado"]


def test_shouryuu_cannon_needs_the_taps_that_follow_the_motion(play) -> None:
    assert play(DOUBLE_QCF_THEN_MASH, super_art="II").moves == ["Shouryuu Cannon"]
    assert play(DOUBLE_QCF_NO_MASH, super_art="II").moves == []


def test_an_unequipped_super_art_cannot_come_out(play) -> None:
    """Mashing on SA I is still Hadou Burst; Shouryuu Cannon is not equipped."""
    assert "Shouryuu Cannon" not in play(DOUBLE_QCF_THEN_MASH, super_art="I").moves
