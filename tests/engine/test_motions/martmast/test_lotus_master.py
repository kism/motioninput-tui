"""Martial Masters, Lotus Master. The one super that is a plain single motion."""

from tests.engine.test_motions.harness import (
    BACK,
    DOWN,
    FORWARD,
    SNES_HP,
    SNES_LK,
    SNES_LP,
    press,
    release,
)


def test_a_half_circle_back_is_the_tower_of_flames(play) -> None:
    """`hcb + P`, filed as a super because it sits under the guide's Supers
    heading. Every other super in the game is a doubled motion, which the
    motion kind alone is enough to recognise; this one is not."""
    script = [
        press(FORWARD, 0),
        press(DOWN, 40),
        release(FORWARD, 80),
        press(BACK, 120),
        release(DOWN, 160),
        press(SNES_HP, 200),
    ]
    attempt = play(script)
    assert attempt.moves == ["Tower Of Flames"]
    move = next(move for move in attempt.session.character.moves if move.name == "Tower Of Flames")
    assert move.category == "super"


def test_the_mirrored_dragon_punch_is_the_pouncing_claw(play) -> None:
    script = [
        press(BACK, 0),
        release(BACK, 60),
        press(DOWN, 60),
        press(BACK, 120),
        press(SNES_LP, 170),
    ]
    assert play(script).moves == ["Pouncing Claw"]


def test_quarter_circle_forward_is_the_bloom(play) -> None:
    script = [press(DOWN, 0), press(FORWARD, 70), release(DOWN, 110), press(SNES_LP, 150)]
    assert play(script).moves == ["Bloom"]


def test_the_same_quarter_circle_on_a_kick_is_the_raising_bloom(play) -> None:
    script = [press(DOWN, 0), press(FORWARD, 70), release(DOWN, 110), press(SNES_LK, 150)]
    assert play(script).moves == ["Raising Bloom"]
