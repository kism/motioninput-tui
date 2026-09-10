"""3rd Strike, Elena. Rhino Horn is hcf+K, Lynx Tail is b, d, db+K."""

from tests.engine.test_motions.harness import (
    BACK,
    DOWN,
    FORWARD,
    HALF_CIRCLE_SKIPPING_DOWN_MK,
    HALF_CIRCLE_THROUGH_DOWN_MK,
    HP,
    MK,
    press,
    release,
)


def test_half_circle_skipping_down_makes_the_expected_directions(play) -> None:
    assert play(HALF_CIRCLE_SKIPPING_DOWN_MK).directions == "← ↙ ↘ →"


def test_half_circle_forward_activates_when_down_alone_is_skipped(play) -> None:
    assert "Rhino Horn" in play(HALF_CIRCLE_SKIPPING_DOWN_MK).moves


def test_half_circle_through_down_makes_the_expected_directions(play) -> None:
    assert play(HALF_CIRCLE_THROUGH_DOWN_MK).directions == "← ↙ ↓ ↘ →"


def test_half_circle_forward_activates_when_down_is_hit(play) -> None:
    assert "Rhino Horn" in play(HALF_CIRCLE_THROUGH_DOWN_MK).moves


def test_back_to_forward_is_not_a_half_circle(play) -> None:
    """Walking back then forward must not count as a half circle."""
    attempt = play([press(BACK, 0), release(BACK, 60), press(FORWARD, 120), press(MK, 160)])
    assert "Rhino Horn" not in attempt.moves


def test_quarter_circle_is_not_a_half_circle(play) -> None:
    """A quarter circle forward has no back in it, so it stays a quarter circle."""
    attempt = play([press(DOWN, 0), press(FORWARD, 70), release(DOWN, 110), press(MK, 150)])
    assert "Rhino Horn" not in attempt.moves


def test_a_half_circle_gets_fourteen_frames_a_step(play) -> None:
    """Half circles are the other place 3rd Strike allows fourteen frames rather
    than ten, so a leisurely 200ms a step is still a Rhino Horn."""
    unhurried = [
        press(BACK, 0),
        release(BACK, 100),
        press(DOWN, 200),
        release(DOWN, 300),
        press(FORWARD, 400),
        press(MK, 430),
    ]
    assert "Rhino Horn" in play(unhurried).moves


def test_healing_is_a_plain_double_quarter_circle(play) -> None:
    """Her third Super Art is written `qcf,qcf + P, then PP to cancel`, and the
    cancel is something the player *may* do rather than part of the command.
    The guide parser used to read the "then" as a follow-up condition and drop
    the move; `p8_cmd_22` in the decompilation is an ordinary `qcf,qcf` on
    punch, like every other super in the game.
    """
    script = [
        press(DOWN, 0),
        press(FORWARD, 40),
        release(DOWN, 80),
        release(FORWARD, 120),
        press(DOWN, 140),
        press(FORWARD, 180),
        press(HP, 200),
    ]
    assert play(script, super_art="III").moves == ["Healing"]
