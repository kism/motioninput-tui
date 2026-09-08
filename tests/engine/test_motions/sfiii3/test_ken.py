"""3rd Strike, Ken.

Two fireballs in a row must not become a super: Shouryuu Reppa is qcf, qcf+P,
so a lenient trainer hands it to anyone who throws two. The game clears the
command buffer when a special comes out, and so does the trainer unless the
loose buffer rule is on.

The shouryuuken here is done the hitbox way, tapping forward twice against a
held down, which never produces a plain forward.
"""

import pytest

from tests.engine.test_motions.harness import DOWN, FORWARD, HP, Script, press, release

# The second fireball starts well clear of the first. Started sooner, the
# forward left over from the first plus the down of the second make a genuine
# forward, down, down-forward, and 3rd Strike gives a shouryuuken for it.
TWO_FIREBALLS: Script = [
    press(DOWN, 0),
    press(FORWARD, 70),
    release(DOWN, 110),
    press(HP, 150),
    release(HP, 190),
    release(FORWARD, 220),
    press(DOWN, 700),
    press(FORWARD, 770),
    release(DOWN, 810),
    press(HP, 850),
]


def double_tap_forward(tap_ms: int, pause_ms: int) -> Script:
    """Hold down and tap forward twice, the hitbox shouryuuken.

    Down is never let go, so the strip is d, df, d, df, d and a plain forward
    never appears at all.
    """
    at = 0
    script = [press(DOWN, at)]
    for _ in range(2):
        at += pause_ms
        script.append(press(FORWARD, at))
        at += tap_ms
        script.append(release(FORWARD, at))
    return [*script, press(HP, at + 40)]


BRISK = double_tap_forward(tap_ms=60, pause_ms=60)
UNHURRIED = double_tap_forward(tap_ms=160, pause_ms=160)
"""Both taps and the pauses at 160ms, so the strip spans 640ms end to end."""


@pytest.mark.parametrize("script", [BRISK, UNHURRIED], ids=["brisk", "unhurried"])
def test_double_tapping_forward_against_held_down_makes_the_expected_directions(play, script) -> None:
    assert play(script).directions == "↓ ↘ ↓ ↘ ↓"


@pytest.mark.parametrize("script", [BRISK, UNHURRIED], ids=["brisk", "unhurried"])
def test_double_tapping_forward_against_held_down_is_a_dragon_punch(play, script) -> None:
    """Down is held rather than pressed as a step, so it must not be timed as one."""
    assert "Shouryuu Ken" in play(script).moves


def test_two_fireballs_stay_two_fireballs(play) -> None:
    assert play(TWO_FIREBALLS).moves == ["Hadou Ken", "Hadou Ken"]


def test_the_second_fireball_does_not_become_a_super(play) -> None:
    assert "Shouryuu Reppa" not in play(TWO_FIREBALLS).moves
