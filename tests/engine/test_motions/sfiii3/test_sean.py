"""3rd Strike, Sean. All three of his Super Arts are ``qcf,qcf + P``.

You equip one before a match, so the trainer does too: only the selected Super
Art can come out, which is the only thing that tells Hadou Burst (SA I),
Shouryuu Cannon (SA II) and Hyper Tornado (SA III) apart. Shouryuu Cannon is
also the one with a "tap P rapidly" tail, so on SA II it activates on the motion
and then wants a follow-through mash.

It is the move the activation freeze was written for: the super's cinematic runs
first and the game reads nothing while it does, so mashing the instant it comes
out is dropped and the taps have to wait it out.
"""

from motioninput_tui.engine.recognizer import FollowUpStatus
from tests.engine.test_motions.harness import DOWN, FORWARD, HP, Script, press, release, taps


def _quarter_circle(at: int) -> Script:
    return [press(DOWN, at), press(FORWARD, at + 50), release(DOWN, at + 90), release(FORWARD, at + 130)]


TWO_QUARTER_CIRCLES: Script = [*_quarter_circle(0), *_quarter_circle(160)]

DOUBLE_QCF: Script = [*TWO_QUARTER_CIRCLES, press(HP, 340), release(HP, 370)]

FREEZE_MS = 833
"""What ``Ruleset.super_freeze_ms`` is set to for this game, which the tap times
below are written around. Pinned by a test rather than imported, so that naming
the game stays the job of this file's path."""

ACTIVATES_AT_MS = 340
"""When the button press above fires the super, and so when its freeze starts."""

READS_AGAIN_AT_MS = ACTIVATES_AT_MS + FREEZE_MS

# Mashed the moment it comes out, which is the mistake: every one of these taps
# lands inside the cinematic and the game never sees them.
DOUBLE_QCF_THEN_EARLY_MASH: Script = [*DOUBLE_QCF, *taps(HP, ACTIVATES_AT_MS + 80, 3, gap_ms=90)]

# The same three taps, waited out and then mashed.
DOUBLE_QCF_THEN_MASH: Script = [*DOUBLE_QCF, *taps(HP, READS_AGAIN_AT_MS + 50, 3, gap_ms=90)]


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
    tried = play(DOUBLE_QCF, super_art="II", settle_ms=FREEZE_MS + 800)
    assert tried.moves == ["Shouryuu Cannon"]
    assert tried.session.activations[0].follow_up.status is FollowUpStatus.MISSED


def test_an_unequipped_super_art_cannot_come_out(play) -> None:
    """Mashing on SA I is still Hadou Burst; Shouryuu Cannon is not equipped."""
    assert "Shouryuu Cannon" not in play(DOUBLE_QCF_THEN_MASH, super_art="I").moves


def test_the_freeze_this_file_is_written_around_is_the_games_own(play) -> None:
    """Pins `FREEZE_MS` to the ruleset, so retuning the game fails here rather
    than quietly moving every tap in this file inside or outside the cinematic."""
    assert play(DOUBLE_QCF).session.game.ruleset.super_freeze_ms == FREEZE_MS


def test_mashing_during_the_cinematic_is_dropped(play) -> None:
    """The super still comes out - the motion earned it - but the taps made
    while the screen is frozen never register, so the follow-through is missed
    exactly as if the player had not mashed at all."""
    rushed = play(DOUBLE_QCF_THEN_EARLY_MASH, super_art="II", settle_ms=FREEZE_MS + 800)
    assert rushed.moves == ["Shouryuu Cannon"]
    follow_up = rushed.session.activations[0].follow_up
    assert follow_up.got == 0
    assert follow_up.status is FollowUpStatus.MISSED


def test_the_follow_through_window_starts_when_the_cinematic_ends(play) -> None:
    """Taps this late would be well past a window measured from the press that
    activated the super; measured from the end of its freeze they are in time."""
    done = play(DOUBLE_QCF_THEN_MASH, super_art="II")
    assert done.session.activations[0].follow_up.status is FollowUpStatus.COMPLETE


def test_each_counted_tap_is_kept_on_the_trail(play) -> None:
    """The trail marks every tap the follow-through took, where it was pressed,
    for the input history to show alongside the super's own motion."""
    done = play(DOUBLE_QCF_THEN_MASH, super_art="II")
    follow_up = done.session.activations[0].follow_up
    tapped = [event.at_ms for event in DOUBLE_QCF_THEN_MASH if event.down and event.key == HP][1:]
    marks = [motion.start_ms for motion in done.session.trail if motion.kind is None]
    assert follow_up.got == follow_up.needed
    assert marks == tapped[: follow_up.got]


def test_taps_the_cinematic_swallowed_leave_no_mark(play) -> None:
    """Nor does the press that fired the super: that one is its motion's."""
    rushed = play(DOUBLE_QCF_THEN_EARLY_MASH, super_art="II", settle_ms=FREEZE_MS + 800)
    assert not any(motion.kind is None for motion in rushed.session.trail)
