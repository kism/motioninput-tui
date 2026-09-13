"""Super Turbo, Sagat. The Tiger Knee is a quarter circle carried on to up-forward.

His guide writes it from down-back, which is only where the quarter circle may
begin, so both starts come out. Super Turbo does not let a diagonal be
skipped, so the forward has to be there before the up-forward.
"""

from tests.engine.test_motions.harness import BACK, DOWN, FORWARD, MK, UP, Script, press, release

TIGER_KNEE_MK: Script = [
    press(DOWN, 0),
    press(FORWARD, 50),  # down-forward
    release(DOWN, 100),  # forward
    press(UP, 150),  # up-forward
    press(MK, 180),
]

# The guide's own version, DB, D, DF, F, UF.
TIGER_KNEE_FROM_DOWN_BACK_MK: Script = [
    press(BACK, 0),
    press(DOWN, 30),  # down-back
    release(BACK, 60),  # down
    press(FORWARD, 100),  # down-forward
    release(DOWN, 150),  # forward
    press(UP, 200),  # up-forward
    press(MK, 230),
]


def test_tiger_knee(play) -> None:
    assert play(TIGER_KNEE_MK).moves == ["Tiger Knee"]


def test_tiger_knee_from_down_back_as_the_guide_writes_it(play) -> None:
    assert play(TIGER_KNEE_FROM_DOWN_BACK_MK).moves == ["Tiger Knee"]
