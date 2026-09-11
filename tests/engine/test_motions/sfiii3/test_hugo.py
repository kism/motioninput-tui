"""3rd Strike, Hugo. What separates a real circle from a half circle and a bit.

Hugo is the reason the rotation matcher is written the way it is: he has `qcb + P`
and `360 + P`, and `hcb + K` and `360 + K`, so every sloppy circle that is really
only most of one lands on a special he did not want. The trainer used to give the
360 on inputs the game does not, which made Moonsault Press feel free here and
rare in the arcade.

The circle is forgiving about *which* directions are hit - a hitbox rolls through
four keys and gets the diagonals from the overlap - and unforgiving about the up
it cannot do without, since that is also a jump. The button has to land while the
jump is still starting; roll round the gate and press afterwards and Hugo leaves
the ground instead, which is what a real 360 feels like and what the trainer used
to hand over every time.
"""

from motioninput_tui.engine.motions import MotionKind
from motioninput_tui.engine.recognizer import LiveMotion
from tests.engine.test_motions.harness import BACK, DOWN, FORWARD, HP, LK, UP, Script, press, release


def _rolled_circle(at: int) -> Script:
    """One revolution on four keys, never letting go: f, df, d, db, b, ub, u."""
    return [
        press(FORWARD, at),
        press(DOWN, at + 40),
        release(FORWARD, at + 80),
        press(BACK, at + 120),
        release(DOWN, at + 160),
        press(UP, at + 200),
        release(BACK, at + 240),
    ]


# The button lands 60ms after the up-back the roll reaches at 200, inside the
# jump's startup. Later than that and Hugo is airborne; see the test below.
ROLLED_CIRCLE: Script = [*_rolled_circle(0), press(HP, 260), release(UP, 320)]

# The same four keys tapped out one at a time, each released before the next.
TAPPED_CIRCLE: Script = [
    press(FORWARD, 0),
    release(FORWARD, 40),
    press(DOWN, 80),
    release(DOWN, 120),
    press(BACK, 160),
    release(BACK, 200),
    press(UP, 240),
    press(HP, 280),
]

# A half circle back carried one notch past back, to up-back: five of the eight,
# which is one more than the plain half circle and four short of a revolution.
ALMOST_A_CIRCLE: Script = [
    press(FORWARD, 0),
    press(DOWN, 50),
    release(FORWARD, 90),
    press(BACK, 130),
    release(DOWN, 170),
    press(UP, 210),
    press(HP, 240),
]

# Two revolutions without a break, for the super.
DOUBLE_CIRCLE: Script = [
    *_rolled_circle(0),
    press(FORWARD, 280),  # uf, carrying straight on round
    release(UP, 320),
    *_rolled_circle(320),
    press(HP, 580),
]


def test_a_rolled_circle_is_the_moonsault_press(play) -> None:
    """It has a quarter circle back inside it, so the 360 has to outrank one."""
    assert play(ROLLED_CIRCLE).moves == ["Moonsault Press"]


def test_the_live_readout_puts_the_circle_over_the_half_circle_inside_it(play) -> None:
    """What the trainer's full-screen panel lists: what a press would complete, at each moment.

    Rolled as far as back, the half circle heads the list. Carried on to up, the
    360 takes over, and the half circle it passed through stays beneath it,
    beaten. Keep holding up and Hugo has jumped, so nothing grounded is left.

    Each spans the directions it was made of, which is what lays it over them
    in the input history: the 360 from forward round to up, the half circle
    from forward to back, the quarter circle inside it from down.
    """
    half = play(_rolled_circle(0)[:5]).session  # f at 0, df, d at 80, db, b at 160
    assert half.live_motions(170) == [LiveMotion(MotionKind.HCB, 0, 160), LiveMotion(MotionKind.QCB, 80, 160)]
    rolled = play(_rolled_circle(0)).session  # ... ub at 200, u at 240
    assert rolled.live_motions(260) == [
        LiveMotion(MotionKind.ROTATE_360, 0, 240),
        LiveMotion(MotionKind.HCB, 0, 160),
        LiveMotion(MotionKind.QCB, 80, 160),
    ]
    assert rolled.live_motions(320) == []


def test_tapping_the_four_keys_quickly_is_the_moonsault_press(play) -> None:
    """The stick is let go three times, and it is still a 360.

    This was once asserted the other way round, on the reasoning that letting go
    ought to break a circle. The decompiled game says otherwise: `check_6` keeps
    a set of which cardinals have been seen and only two timers can wipe it, so a
    release costs nothing but the time it takes. What makes a 360 hard is the
    pace, which is what `test_tapping_the_four_keys_slowly_is_nothing` covers.

    Note that no Giant Palm Bomber falls out of it either. That table is
    `d, db, b` compared for equality, and tapping down and then back never
    produces the down-back in the middle.
    """
    assert play(TAPPED_CIRCLE).moves == ["Moonsault Press"]


def test_tapping_the_four_keys_slowly_is_nothing(play) -> None:
    """The same four keys, a shade over fourteen frames apart.

    Every tap lands, but the set of cardinals is wiped between each one, so the
    game never holds more than one of them at a time.
    """
    slow: Script = [
        press(FORWARD, 0),
        release(FORWARD, 40),
        press(DOWN, 300),
        release(DOWN, 340),
        press(BACK, 600),
        release(BACK, 640),
        press(UP, 900),
        press(HP, 940),
    ]
    assert play(slow).moves == []


def test_a_half_circle_and_a_bit_is_not_a_circle(play) -> None:
    """Five of the eight directions is not a revolution, however cleanly rolled."""
    assert play(ALMOST_A_CIRCLE).moves == ["Giant Palm Bomber"]


def test_the_same_roll_with_a_kick_is_the_meat_squasher(play) -> None:
    """His other 360, and the one that has to beat `hcb + K` rather than qcb."""
    kicked: Script = [*_rolled_circle(0), press(LK, 260), release(UP, 320)]
    assert play(kicked).moves == ["Meat Squasher"]


def test_two_revolutions_are_the_gigas_breaker(play) -> None:
    """The 720 outranks the 360 the first revolution already earned."""
    assert play(DOUBLE_CIRCLE, super_art="I").moves == ["Gigas Breaker"]


def test_one_revolution_is_not_the_gigas_breaker(play) -> None:
    assert "Gigas Breaker" not in play(ROLLED_CIRCLE, super_art="I").moves


def test_finishing_the_circle_and_then_pressing_is_a_jump(play) -> None:
    """The same roll with the button a few frames later than `ROLLED_CIRCLE`.

    The circle is complete and quick enough, and the game still gives nothing:
    `check_special_attack` runs before `check_jump_ready` and only while Hugo is
    on the ground, so the up-back at 200 starts a jump that the button at 300 is
    far too late for. This is the difference between a 360 that lands every time
    in a trainer and one that lands half the time in the arcade.

    Nothing means nothing. The quarter circle back inside the roll must not pay
    out a Giant Palm Bomber as a consolation prize either - Hugo is in the air,
    and the air is not where any of this happens.
    """
    dawdled: Script = [*_rolled_circle(0), press(HP, 300), release(UP, 340)]
    assert play(dawdled).moves == []


def test_a_half_circle_that_overshoots_to_up_back_is_a_jump(play) -> None:
    """Not a 360 at all, and the reason the jump rule cannot live in the 360.

    A missed circle used to fall through to `hcb + K` and hand over an Ultra
    Throw, which is the wrong lesson twice over: the motion was not a circle,
    and the up-back that spoiled it had already put Hugo in the air. Every
    grounded move is judged on this, not just the rotations.
    """
    overshot: Script = [
        press(FORWARD, 0),
        press(DOWN, 60),
        release(FORWARD, 100),
        press(BACK, 140),
        release(DOWN, 180),
        press(UP, 220),  # up-back, since back is still held: the jump starts here
        press(LK, 300),
    ]
    assert play(overshot).moves == []


def test_the_same_half_circle_stopping_at_back_is_the_ultra_throw(play) -> None:
    """The overshoot is what costs it, not the pace."""
    clean: Script = [
        press(FORWARD, 0),
        press(DOWN, 60),
        release(FORWARD, 100),
        press(BACK, 140),
        release(DOWN, 180),
        press(LK, 220),
    ]
    assert play(clean).moves == ["Ultra Throw"]
