"""KoF '98, Chizuru Kagura. A double tap is two separate taps, not a roll."""

from tests.engine.test_motions.harness import BACK, DOWN, FORWARD, NEO_A, press, release

CHOUMON = "202 Katsu Otsu Shiki Choumonnoisshin"


def test_down_tapped_twice_is_choumon(play) -> None:
    script = [press(DOWN, 0), release(DOWN, 60), press(DOWN, 120), press(NEO_A, 160)]
    assert CHOUMON in play(script).moves


def test_rolling_down_back_to_down_is_not_a_double_tap(play) -> None:
    script = [press(DOWN, 0), press(BACK, 10), release(BACK, 120), press(NEO_A, 160)]
    assert CHOUMON not in play(script).moves


def test_a_quarter_circle_is_not_a_double_tap(play) -> None:
    script = [press(DOWN, 0), press(FORWARD, 60), release(DOWN, 120), press(NEO_A, 160)]
    assert CHOUMON not in play(script).moves
