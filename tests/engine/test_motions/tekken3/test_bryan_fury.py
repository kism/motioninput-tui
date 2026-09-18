"""Tekken 3, Bryan Fury. Strings, dashes and one quarter circle.

The only 3D game here, and the only one whose move list is mostly runs of
presses rather than motions. One button per limb, so the panel is two keys wide
and none of the shared scripts fit it - they all press a third button the
Tekken set leaves unbound.
"""

from tests.engine.test_motions.harness import (
    BACK,
    DOWN,
    FORWARD,
    TEKKEN_LK,
    TEKKEN_LP,
    TEKKEN_RK,
    TEKKEN_RP,
    Script,
    press,
    release,
)


def _tap(key: str, at_ms: int) -> Script:
    return [press(key, at_ms), release(key, at_ms + 40)]


def test_two_presses_are_the_one_two(play) -> None:
    assert play([*_tap(TEKKEN_LP, 0), press(TEKKEN_RP, 180)]).moves == ["One Two"]


def test_a_third_press_carries_it_on(play) -> None:
    """`lp,rp,lk`. The same two presses start it, and the kick makes it the
    longer move - which is the whole of how this game's move list works."""
    script = [*_tap(TEKKEN_LP, 0), *_tap(TEKKEN_RP, 180), press(TEKKEN_LK, 360)]
    assert play(script).moves[-1] == "One Two -> Kick"


def test_a_string_can_start_from_a_direction(play) -> None:
    """`df+lp,rp` is the Elbow Pistons: crouch into the first press, then the
    second. Read as "hold down-forward and press both" it would be a move Bryan
    does not have."""
    script = [press(DOWN, 0), press(FORWARD, 20), *_tap(TEKKEN_LP, 80), press(TEKKEN_RP, 260)]
    assert play(script).moves[-1] == "Elbow Pistons (NJ)"


def test_forward_twice_and_a_punch_is_the_straight_fist(play) -> None:
    """The dash: `f,F` is tap forward then hold it, which the trainer reads as
    the two taps it models."""
    script = [
        press(FORWARD, 0),
        release(FORWARD, 60),
        press(FORWARD, 140),
        press(TEKKEN_RP, 200),
    ]
    assert play(script).moves == ["Straight Fist"]


def test_one_forward_is_not_a_dash(play) -> None:
    """Holding forward the whole time is one span of it, not two, so it gives
    the move on a held forward rather than the dash."""
    assert play([press(FORWARD, 0), press(TEKKEN_RP, 200)]).moves != ["Straight Fist"]


def test_back_twice_and_a_kick_is_the_somersault(play) -> None:
    script = [press(BACK, 0), release(BACK, 60), press(BACK, 140), press(TEKKEN_RK, 200)]
    assert play(script).moves == ["Flying Somersault Kick"]


def test_a_single_back_and_a_kick_is_the_knee(play) -> None:
    """`b+rk`, the plain held direction, which is what the double tap has to be
    told apart from."""
    assert play([press(BACK, 0), press(TEKKEN_RK, 200)]).moves == ["Knee"]


def test_this_game_does_have_a_quarter_circle(play) -> None:
    """Most of the roster is presses, but not all of it."""
    script = [press(DOWN, 0), press(FORWARD, 70), release(DOWN, 110), press(TEKKEN_RP, 150)]
    assert play(script).moves == ["Gutpunch"]


def test_the_chain_off_the_gutpunch_needs_the_gutpunch(play) -> None:
    """The guide marks a row `^` to say it continues the one above. Bryan's
    Double Punishment is a plain `b+rp` once the Gutpunch is out, and his
    Spinning Punch otherwise."""
    quarter = [press(DOWN, 0), press(FORWARD, 70), release(DOWN, 110), press(TEKKEN_RP, 150)]
    after = [release(FORWARD, 220), release(TEKKEN_RP, 220), press(BACK, 300), press(TEKKEN_RP, 360)]
    assert play([*quarter, *after]).moves[-1].startswith("Double Punishment")
