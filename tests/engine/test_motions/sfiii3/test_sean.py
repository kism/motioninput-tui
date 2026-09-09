"""3rd Strike, Sean. All three of his Super Arts are ``qcf,qcf + P``.

You equip one before a match, so the trainer does too: only the selected Super
Art can come out, which is the only thing that tells Hadou Burst (SA I),
Shouryuu Cannon (SA II) and Hyper Tornado (SA III) apart. Shouryuu Cannon is
also the one with a "tap P rapidly" tail, so on SA II it activates on the motion
and then wants a follow-through mash.
"""

from motioninput_tui.engine.recognizer import FollowUpStatus
from tests.engine.test_motions.harness import DOWN, FORWARD, HP, Script, press, release, taps


def _quarter_circle(at: int) -> Script:
    return [press(DOWN, at), press(FORWARD, at + 50), release(DOWN, at + 90), release(FORWARD, at + 130)]


TWO_QUARTER_CIRCLES: Script = [*_quarter_circle(0), *_quarter_circle(160)]

DOUBLE_QCF: Script = [*TWO_QUARTER_CIRCLES, press(HP, 340), release(HP, 370)]

DOUBLE_QCF_THEN_MASH: Script = [*DOUBLE_QCF, *taps(HP, 420, 3, gap_ms=90)]


def test_the_first_super_art_is_equipped_to_start_with(play) -> None:
    assert play(DOUBLE_QCF).moves == ["Hadou Burst"]


def test_each_super_art_answers_the_same_motion_differently(play) -> None:
    """The same input, three answers: this is the whole point of selecting one."""
    assert play(DOUBLE_QCF, super_art="I").moves == ["Hadou Burst"]
    assert play(DOUBLE_QCF, super_art="III").moves == ["Hyper Tornado"]


def test_shouryuu_cannon_activates_on_the_motion_then_wants_the_mash(play) -> None:
    """The motion fires it (phase 1); the taps that follow complete it."""
    done = play(DOUBLE_QCF_THEN_MASH, super_art="II")
    assert done.moves == ["Shouryuu Cannon"]
    assert done.session.activations[0].follow_up.status is FollowUpStatus.COMPLETE


def test_shouryuu_cannon_without_the_mash_still_comes_out_but_is_marked_missed(play) -> None:
    """It used to be complete silence; now the motion counts and the missing
    follow-through is fed back."""
    tried = play(DOUBLE_QCF, super_art="II", settle_ms=800)
    assert tried.moves == ["Shouryuu Cannon"]
    assert tried.session.activations[0].follow_up.status is FollowUpStatus.MISSED


def test_an_unequipped_super_art_cannot_come_out(play) -> None:
    """Mashing on SA I is still Hadou Burst; Shouryuu Cannon is not equipped."""
    assert "Shouryuu Cannon" not in play(DOUBLE_QCF_THEN_MASH, super_art="I").moves
