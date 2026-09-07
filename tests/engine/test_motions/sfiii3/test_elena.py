"""3rd Strike, Elena. Rhino Horn is hcf+K, Lynx Tail is b, d, db+K."""

from __future__ import annotations

from tests.engine.test_motions.harness import BACK, DOWN, FORWARD, MK, Script, press, release

# Back, then add down, then add forward. Pressing forward while back is still
# held gives down-forward straight away, so a plain down never appears. This is
# an ordinary hitbox half circle and the game accepts it.
HALF_CIRCLE_SKIPPING_DOWN: Script = [
    press(BACK, 0),
    press(DOWN, 60),
    press(FORWARD, 120),
    release(DOWN, 180),
    release(BACK, 185),
    press(MK, 220),
]

# The same move rolled cleanly through every direction.
HALF_CIRCLE_THROUGH_DOWN: Script = [
    press(BACK, 0),
    press(DOWN, 60),
    release(BACK, 100),
    press(FORWARD, 140),
    release(DOWN, 180),
    press(MK, 220),
]


def test_half_circle_skipping_down_makes_the_expected_directions(play) -> None:
    assert play(HALF_CIRCLE_SKIPPING_DOWN).directions == "← ↙ ↘ →"


def test_half_circle_forward_activates_when_down_alone_is_skipped(play) -> None:
    assert "Rhino Horn" in play(HALF_CIRCLE_SKIPPING_DOWN).moves


def test_half_circle_through_down_makes_the_expected_directions(play) -> None:
    assert play(HALF_CIRCLE_THROUGH_DOWN).directions == "← ↙ ↓ ↘ →"


def test_half_circle_forward_activates_when_down_is_hit(play) -> None:
    assert "Rhino Horn" in play(HALF_CIRCLE_THROUGH_DOWN).moves


def test_back_to_forward_is_not_a_half_circle(play) -> None:
    """Walking back then forward must not count as a half circle."""
    attempt = play([press(BACK, 0), release(BACK, 60), press(FORWARD, 120), press(MK, 160)])
    assert "Rhino Horn" not in attempt.moves


def test_quarter_circle_is_not_a_half_circle(play) -> None:
    """A quarter circle forward has no back in it, so it stays a quarter circle."""
    attempt = play([press(DOWN, 0), press(FORWARD, 70), release(DOWN, 110), press(MK, 150)])
    assert "Rhino Horn" not in attempt.moves
