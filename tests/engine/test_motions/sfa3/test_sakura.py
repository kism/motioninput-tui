"""Alpha 3, Sakura. Sakura Otoshi is the same two-phase move as in USFIV:
`f,d,df + K` starts the hop, then up to three deliberate P taps add hits.

It is also the counterpart to `sfiii3/test_sean.py`: a two-phase *special*
rather than a super, so none of Alpha 3's activation freeze applies and the taps
are read the moment the move comes out.

Midare-zakura sits on top of it, and is the roster's one corrected command. The
guide gives it as `qcf,d,df + K`; the move is `qcf,qcf + K`, like her other two
supers, so `datagen/commands.py` overrides it. The guide's version parsed and
came out perfectly well in the trainer, which is exactly why the mistake needed
correcting at the source rather than being noticed as a bug: nothing was broken,
the trainer was just faithfully teaching an input Alpha 3 does not accept.
"""

from motioninput_tui.engine.recognizer import FollowUpStatus
from tests.engine.test_motions.harness import DOWN, FORWARD, HP, LK, LP, Script, press, release, taps


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


# `qcf,qcf + K`, on a hitbox: the two quarter circles with forward let go
# between them, which is how a player actually does a double motion.
MIDARE_ZAKURA: Script = [
    press(DOWN, 0),  # d
    press(FORWARD, 40),  # df
    release(DOWN, 80),  # f
    release(FORWARD, 120),  # neutral
    press(DOWN, 160),  # d
    press(FORWARD, 200),  # df
    release(DOWN, 240),  # f
    press(LK, 280),
]

# The guide's own `qcf,d,df + K`: a quarter circle into a dragon punch, sharing
# the forward. It has to give the dragon punch move on that button instead.
THE_GUIDES_VERSION: Script = [
    press(DOWN, 0),  # d
    press(FORWARD, 40),  # df
    release(DOWN, 80),  # f
    press(DOWN, 120),  # df
    release(FORWARD, 160),  # d
    press(FORWARD, 200),  # df
    press(LK, 240),
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


def test_a_special_with_a_tail_has_no_activation_cinematic(play) -> None:
    """Alpha 3 freezes the screen for its supers, and this is not one. Taps this
    soon after activation would all be swallowed if the freeze applied to every
    move with a tail; here they land and finish it."""
    done = play([*_sakura_otoshi(), *taps(LP, 300, 3, gap_ms=180)])
    follow_up = done.session.activations[0].follow_up
    assert not follow_up.frozen
    assert follow_up.status is FollowUpStatus.COMPLETE


def test_midare_zakura_is_two_quarter_circles(play) -> None:
    assert play(MIDARE_ZAKURA).moves == ["Midare-zakura"]


def test_midare_zakura_survives_an_inferred_terminal(play) -> None:
    """Not just on a terminal that reports key releases. A motion this long is
    where the inferred path would be expected to fall over first."""
    assert play(MIDARE_ZAKURA, exact_input=False).moves == ["Midare-zakura"]


def test_the_guides_version_of_the_command_is_not_the_super(play) -> None:
    """The correction, from the other side: `qcf,d,df + K` is a real input that
    Alpha 3 answers with Sakura Otoshi, the dragon punch on the end of it. If
    this ever gives Midare-zakura again the override has been lost."""
    assert play(THE_GUIDES_VERSION).moves == ["Sakura Otoshi"]


def test_a_punch_on_the_same_motion_is_the_shinkuu_hadouken(play) -> None:
    """Worth pinning: the motion is right and only the button is wrong, which
    looks identical on the input strip."""
    assert play([*MIDARE_ZAKURA[:-1], press(HP, 280)]).moves == ["Shinkuu Hadou Ken"]
