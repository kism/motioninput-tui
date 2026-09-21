"""USFIV, Akuma. The Raging Demon, which is a run of presses rather than a motion.

He has two of them and they differ by one direction in the middle - `LP,LP,f,
LK,HP` is the Shun Goku Satsu and `LP,LP,b,LK,HP` the Wrath of the Raging
Demon. Nothing else in the trainer turns on so little, which is why this is
where `MotionKind.SEQUENCE` is checked: the four presses are identical in both.
"""

from tests.engine.test_motions.harness import BACK, FORWARD, HP, LK, LP, Script, press, release

SLOW_MS = 2200
"""Past `sequence_window_ms`, so the run has taken too long to be one input."""


def _demon(direction: str, *, last_at: int = 600) -> Script:
    """`LP, LP, <direction> + LK, HP`, at a pace a player could manage."""
    return [
        press(LP, 0),
        release(LP, 40),
        press(LP, 200),
        release(LP, 240),
        press(direction, 380),
        press(LK, 420),
        release(LK, 460),
        press(HP, last_at),
    ]


def test_the_forward_demon_is_the_shun_goku_satsu(play) -> None:
    assert play(_demon(FORWARD)).moves == ["Shun Goku Satsu"]


def test_the_back_demon_is_the_wrath_of_the_raging_demon(play) -> None:
    """The same four presses. Only the direction held for the kick differs."""
    assert play(_demon(BACK)).moves == ["Wrath of the Raging Demon"]


def test_without_the_direction_neither_comes_out(play) -> None:
    assert play([event for event in _demon(FORWARD) if event.key != FORWARD]).moves == []


def test_a_run_that_takes_too_long_is_not_one_input(play) -> None:
    assert play(_demon(FORWARD, last_at=SLOW_MS)).moves == []


def test_a_stray_press_in_the_middle_breaks_it(play) -> None:
    """The steps have to be the run, not merely end it: fumbling a button is
    how the games drop a string, and letting it through would hand the move to
    someone who did not do it."""
    script = _demon(FORWARD)
    stray = [press(LK, 300), release(LK, 340)]
    assert play([*script[:4], *stray, *script[4:]]).moves == []


def test_the_last_press_on_its_own_is_nothing(play) -> None:
    assert play([press(HP, 0)]).moves == []
