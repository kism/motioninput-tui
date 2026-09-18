"""Martial Masters, Scorpion. Diagonals cannot be skipped, and the two dragon punch sides."""

from tests.engine.test_motions.harness import (
    BACK,
    DOWN,
    FORWARD,
    HALF_CIRCLE_SKIPPING_DOWN_MK,
    HALF_CIRCLE_THROUGH_DOWN_MK,
    SNES_HP,
    SNES_LK,
    SNES_LP,
    press,
    release,
)


def test_a_clean_half_circle_forward_is_the_desert_crawl(play) -> None:
    """The shared script, unchanged. Its `MK` is the key this panel calls `HK`,
    which is why the half circle scripts work here and the `HP` ones do not."""
    assert play(HALF_CIRCLE_THROUGH_DOWN_MK).moves == ["Desert Crawl"]


def test_a_half_circle_that_skips_down_gives_the_command_normal(play) -> None:
    """The same keys at the same moments that 3rd Strike reads as a half circle,
    because it only wants three of the five points. This game is not told it may
    do that, so the motion is a step short - and since the script is still
    holding forward when the button lands, out comes `f + HK` instead."""
    assert play(HALF_CIRCLE_SKIPPING_DOWN_MK).moves == ["Pincher Kick"]


def test_dragon_punch_forward_is_the_aculeus_sting(play) -> None:
    script = [
        press(FORWARD, 0),
        release(FORWARD, 60),
        press(DOWN, 60),
        press(FORWARD, 120),
        press(SNES_LP, 170),
    ]
    assert play(script).moves == ["Aculeus Sting"]


def test_dragon_punch_back_is_the_predator_crash(play) -> None:
    """`b,d,db + P`. The same shape mirrored, and on the same button, so the
    trainer has only the side to go on."""
    script = [
        press(BACK, 0),
        release(BACK, 60),
        press(DOWN, 60),
        press(BACK, 120),
        press(SNES_LP, 170),
    ]
    assert play(script).moves == ["Predator Crash"]


def test_the_same_back_motion_on_a_kick_is_the_fake(play) -> None:
    script = [
        press(BACK, 0),
        release(BACK, 60),
        press(DOWN, 60),
        press(BACK, 120),
        press(SNES_LK, 170),
    ]
    assert play(script).moves == ["Predator Crash Fake"]


def test_a_half_circle_back_is_the_death_roll(play) -> None:
    script = [
        press(FORWARD, 0),
        press(DOWN, 40),
        release(FORWARD, 80),
        press(BACK, 120),
        release(DOWN, 160),
        press(SNES_LK, 200),
    ]
    assert play(script).moves == ["Death Roll"]


def test_double_quarter_circle_forward_is_the_super(play) -> None:
    script = [
        press(DOWN, 0),
        press(FORWARD, 60),
        release(DOWN, 100),
        release(FORWARD, 140),
        press(DOWN, 180),
        press(FORWARD, 240),
        release(DOWN, 280),
        press(SNES_HP, 320),
    ]
    assert play(script).moves[-1] == "Merciless Feast"
