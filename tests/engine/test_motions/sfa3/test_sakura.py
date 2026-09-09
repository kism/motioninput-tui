"""Alpha 3, Sakura. Sakura Otoshi is the same two-phase move as in USFIV:
`f,d,df + K` starts the hop, then up to three deliberate P taps add hits.
"""

from motioninput_tui.engine.recognizer import FollowUpStatus
from tests.engine.test_motions.harness import DOWN, FORWARD, LK, LP, Script, press, release, taps


def _sakura_otoshi() -> Script:
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


def test_sakura_otoshi_activates_on_the_motion(play) -> None:
    done = play(_sakura_otoshi(), settle_ms=100)
    assert done.moves == ["Sakura Otoshi"]
    assert done.session.activations[0].follow_up.status is FollowUpStatus.PENDING


def test_three_deliberate_p_taps_complete_it(play) -> None:
    done = play([*_sakura_otoshi(), *taps(LP, 400, 3, gap_ms=180)])
    assert done.session.activations[0].follow_up.status is FollowUpStatus.COMPLETE


def test_no_follow_through_is_marked_missed(play) -> None:
    done = play(_sakura_otoshi(), settle_ms=700)
    assert done.session.activations[0].follow_up.status is FollowUpStatus.MISSED
