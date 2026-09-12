"""Ultra SF4, Elena. Rhino Horn is hcf+K, and here a half circle has to hit the down.

3rd Strike reads one at three points, so any down will do there
(`sfiii3/test_elena.py`); this game wants all five directions.
"""

from tests.engine.test_motions.harness import HALF_CIRCLE_SKIPPING_DOWN_MK, HALF_CIRCLE_THROUGH_DOWN_MK


def test_a_half_circle_that_skips_the_down_is_not_one(play) -> None:
    assert "Rhino Horn" not in play(HALF_CIRCLE_SKIPPING_DOWN_MK).moves


def test_a_half_circle_through_the_down_is_the_rhino_horn(play) -> None:
    assert "Rhino Horn" in play(HALF_CIRCLE_THROUGH_DOWN_MK).moves
