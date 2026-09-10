"""Ultra SF4, Zangief. The 360 is forgiving about aim, not about letting go.

A hitbox never touches six of the eight directions on purpose: it rolls through
four keys and the diagonals come from the overlap, which is what `rotation_slack`
allows for. What it will not allow is a neutral - releasing every key mid-circle
means the hand came off the stick, and no game gives you a 360 for that.
"""

from tests.engine.test_motions.harness import BACK, DOWN, FORWARD, HP, LP, UP, press, release

# Rolled: the next key goes down before the last comes up, so the stick is never
# let go and the diagonals appear between the cardinals.
ROLLED_CIRCLE = [
    press(FORWARD, 0),
    press(DOWN, 50),
    release(FORWARD, 90),
    press(BACK, 130),
    release(DOWN, 170),
    press(UP, 210),
    release(BACK, 250),
    press(LP, 270),
    release(UP, 300),
]

# The same four keys, each fully released before the next: four separate taps
# with the stick at neutral in between.
TAPPED_CIRCLE = [
    press(FORWARD, 0),
    release(FORWARD, 40),
    press(DOWN, 80),
    release(DOWN, 120),
    press(BACK, 160),
    release(BACK, 200),
    press(UP, 240),
    press(LP, 260),
    release(UP, 300),
]


def test_a_rolled_circle_is_a_spinning_piledriver(play) -> None:
    """Four keys rolled without letting go travels six of the eight directions,
    which `rotation_slack = 2` accepts as the whole revolution."""
    assert play(ROLLED_CIRCLE).moves == ["Spinning Piledriver"]


def test_tapping_the_same_four_keys_is_not_a_circle(play) -> None:
    """The neutral between each tap restarts the circle every time, so this
    never accumulates one. It used to give an SPD on every attempt, which is why
    the trainer's 360 landed far more readily than the game's."""
    assert play(TAPPED_CIRCLE).moves == []


def test_letting_go_part_way_round_restarts_the_circle(play) -> None:
    """Even one full release mid-roll is enough to lose it."""
    script = [
        press(FORWARD, 0),
        press(DOWN, 50),
        release(FORWARD, 90),
        release(DOWN, 130),
        press(BACK, 170),
        press(UP, 210),
        release(BACK, 250),
        press(LP, 270),
    ]
    assert play(script).moves == []


def test_dragon_punch_motion_is_banishing_flat_not_the_spd(play) -> None:
    """f, d, df + P is Zangief's Banishing Flat; the rotation must not steal it."""
    script = [
        press(FORWARD, 0),
        release(FORWARD, 40),
        press(DOWN, 70),
        press(FORWARD, 120),
        release(DOWN, 200),
        press(HP, 210),
        release(FORWARD, 240),
    ]
    assert play(script).moves == ["Banishing Flat"]
