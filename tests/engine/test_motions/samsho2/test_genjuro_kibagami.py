"""Samurai Shodown II, Genjuro Kibagami. The SanRenSatsu, three of one motion.

Worth a file of its own because the whole string is the *same* quarter circle
on the same pair of buttons three times over. Nothing about the input says
which of the three you are doing; only how many have already landed does, which
is the plainest case for chains in the trainer.
"""

from tests.engine.test_motions.harness import DOWN, FORWARD, NEO_A, Script, press, release


def _quarter_circle(at_ms: int) -> Script:
    return [
        press(DOWN, at_ms),
        press(FORWARD, at_ms + 60),
        release(DOWN, at_ms + 100),
        press(NEO_A, at_ms + 140),
        release(FORWARD, at_ms + 200),
        release(NEO_A, at_ms + 200),
    ]


def test_one_quarter_circle_is_the_first_hit(play) -> None:
    assert play(_quarter_circle(0)).moves == ["SanRenSatsu Kiba"]


def test_three_of_them_are_the_whole_string(play) -> None:
    script = [*_quarter_circle(0), *_quarter_circle(260), *_quarter_circle(520)]
    assert play(script).moves == ["SanRenSatsu Kiba", "SanRenSatsu Tsuno", "SanRenSatu Rin"]


def test_a_pause_drops_you_back_to_the_first_hit(play) -> None:
    """The string closes with the window, so the next quarter circle starts it
    over rather than carrying on from where it left off."""
    script = [*_quarter_circle(0), *_quarter_circle(1200)]
    assert play(script).moves == ["SanRenSatsu Kiba", "SanRenSatsu Kiba"]
