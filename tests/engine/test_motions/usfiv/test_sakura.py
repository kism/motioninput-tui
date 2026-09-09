"""Ultra SF4, Sakura. Her two qcb,qcb supers differ only by button count, so
the three-kick one must not be eaten by the one-kick one landing first; and
Sakura Otoshi is the two-phase move (dp + K, then three deliberate P taps).
"""

from motioninput_tui.engine.recognizer import FollowUpStatus
from tests.engine.test_motions.harness import BACK, DOWN, FORWARD, HK, LK, LP, MK, Script, press, release, taps


def _sakura_otoshi() -> Script:
    """f, d, df + K — the motion that starts Sakura Otoshi."""
    return [
        press(FORWARD, 0),
        release(FORWARD, 40),
        press(DOWN, 70),
        press(FORWARD, 120),
        release(DOWN, 200),
        press(LK, 210),
        release(LK, 250),
        release(FORWARD, 260),
    ]


def _double_qcb(*buttons: str) -> Script:
    """qcb, qcb, then the given kicks pressed together at the end."""
    return [
        press(DOWN, 0),
        press(BACK, 60),
        release(DOWN, 100),
        release(BACK, 150),
        press(DOWN, 200),
        press(BACK, 260),
        release(DOWN, 300),
        *(press(button, 340 + i * 8) for i, button in enumerate(buttons)),
        *(release(button, 400 + i * 8) for i, button in enumerate(buttons)),
    ]


def test_three_kicks_is_the_kkk_super(play) -> None:
    """qcb,qcb + KKK is Haru Ranman, not Haru Ichiban (qcb,qcb + K)."""
    assert play(_double_qcb(HK, MK, LK)).moves == ["Haru Ranman"]


def test_one_kick_is_the_k_super(play) -> None:
    """A single kick on the same motion still gives Haru Ichiban, once the
    grace window for the other two has passed."""
    assert play(_double_qcb(LK)).moves == ["Haru Ichiban"]


def test_sakura_otoshi_activates_on_the_motion(play) -> None:
    """The dp + K fires it straight away, follow-through still expected."""
    done = play(_sakura_otoshi(), settle_ms=100)
    assert done.moves == ["Sakura Otoshi"]
    assert done.session.activations[0].follow_up.status is FollowUpStatus.PENDING


def test_three_deliberate_p_taps_complete_it(play) -> None:
    done = play([*_sakura_otoshi(), *taps(LP, 400, 3, gap_ms=180)])
    assert done.session.activations[0].follow_up.status is FollowUpStatus.COMPLETE
    assert done.moves == ["Sakura Otoshi"]


def test_no_follow_through_is_marked_missed(play) -> None:
    done = play(_sakura_otoshi(), settle_ms=700)
    assert done.session.activations[0].follow_up.status is FollowUpStatus.MISSED


def test_a_mashed_burst_is_not_the_deliberate_taps(play) -> None:
    """Rhythm rejects a single fast burst: presses closer than 70ms don't count."""
    done = play([*_sakura_otoshi(), *taps(LP, 400, 3, gap_ms=25)], settle_ms=700)
    assert done.session.activations[0].follow_up.status is FollowUpStatus.MISSED
