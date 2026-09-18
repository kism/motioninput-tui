"""3rd Strike, Dudley. The Ducking, and the two moves that come out of it.

The guide writes these the way the Street Fighter guides write every chain,
with the parent on the end: `Press P during Ducking`. So a bare punch is
nothing on its own and the Ducking Straight once the Ducking is out, which is
the same mechanism the Neo Geo guides reach by naming the parent first.

`chain_window_ms` is the one figure in this game's ruleset that is reckoned
rather than read out of the decompilation - see
`docs/sfiii3-from-the-decomp.md`.
"""

from tests.engine.test_motions.harness import (
    BACK,
    DOWN,
    FORWARD,
    HP,
    MK,
    Script,
    press,
    release,
)

DUCKING: Script = [
    press(BACK, 0),
    press(DOWN, 50),
    release(BACK, 90),
    press(FORWARD, 130),
    release(DOWN, 170),
    press(MK, 210),
    release(MK, 260),
]


def test_the_half_circle_forward_is_the_ducking(play) -> None:
    assert play(DUCKING).moves == ["Ducking"]


def test_a_punch_out_of_it_is_the_ducking_straight(play) -> None:
    assert play([*DUCKING, press(HP, 400)]).moves == ["Ducking", "Ducking Straight"]


def test_a_kick_out_of_it_is_the_ducking_upper(play) -> None:
    assert play([*DUCKING, press(MK, 400)]).moves == ["Ducking", "Ducking Upper"]


def test_a_punch_on_its_own_is_nothing(play) -> None:
    """Which is why the link cannot simply sit in the move list: a bare button
    has to stay unread until the Ducking has opened the way to it."""
    assert play([press(HP, 0)]).moves == []


def test_the_link_is_gone_once_the_window_passes(play) -> None:
    """Forward is let go first: the script is still holding it from the half
    circle, and `f + HP` is his Step Straight, a real command normal."""
    assert play([*DUCKING, release(FORWARD, 1100), press(HP, 1200)]).moves == ["Ducking"]
