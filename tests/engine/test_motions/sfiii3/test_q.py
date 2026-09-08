"""3rd Strike, Q.

Q is a single-letter character heading in the FAQ (`Q, Whose Existence is a
Mystery`), so the roster is only complete if the parser accepts a one-character
name. The move names are the abridged romaji the guide uses.
"""

from tests.engine.test_motions.harness import BACK, DOWN, LP, Script, press, release

# Down, down-back, back: an ordinary quarter circle back on the hitbox.
QUARTER_CIRCLE_BACK_LP: Script = [
    press(DOWN, 0),
    press(BACK, 70),
    release(DOWN, 110),
    press(LP, 150),
]


def test_q_is_in_the_roster(play) -> None:
    """A bare 'Q' heading must not be skipped as too short to be a name."""
    assert play([press(LP, 0)]) is not None


def test_quarter_circle_back_punch_is_the_hand_swipe(play) -> None:
    assert "Kousokudo Renzoku Dageki (Kari)" in play(QUARTER_CIRCLE_BACK_LP).moves
