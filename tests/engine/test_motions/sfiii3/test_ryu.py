"""3rd Strike, Ryu. The dragon punch shortcut lives here and nowhere else.

Compare `sfa3/test_ryu.py` and `hsf2/test_ryu.py`, which play the same script.
"""

from tests.engine.test_motions.harness import (
    DOWN,
    DOWN_DOUBLE_TAP_FORWARD_HP,
    FORWARD,
    HP,
    QUARTER_BACK_ROLLED_TO_FORWARD_HP,
    QUARTER_CIRCLE_FORWARD_HP,
    press,
    release,
)


def test_quarter_circle_forward_is_a_fireball(play) -> None:
    assert play(QUARTER_CIRCLE_FORWARD_HP).moves == ["Hadou Ken"]


def test_hold_down_double_tap_forward_is_a_dragon_punch(play) -> None:
    """3rd Strike accepts d, f, f as a shouryuuken. This is the headline difference."""
    assert "Shouryuu Ken" in play(DOWN_DOUBLE_TAP_FORWARD_HP).moves


def test_the_snk_roll_is_only_a_fireball_here(play) -> None:
    """`d,db,b,db,f` is Terry's Power Geyser in KoF '98. Street Fighter has no
    move on it at all, and the sweep from back round to forward is read as the
    quarter circle it passes through on the way."""
    assert play(QUARTER_BACK_ROLLED_TO_FORWARD_HP).moves == ["Hadou Ken"]


# The three below are read off the decompiled game rather than inferred from a
# guide. See `docs/sfiii3-from-the-decomp.md` for how its command tables spell
# these motions out.


def test_down_then_forward_with_no_diagonal_is_not_a_fireball(play) -> None:
    """`check_0` compares the lever for equality and the table says `d, df, f`,
    so the down-forward is not optional. A hitbox player who lets go of down
    before pressing forward gets nothing - the one place 3rd Strike is stricter
    than the other Street Fighters here, not looser."""
    attempt = play([press(DOWN, 0), release(DOWN, 40), press(FORWARD, 60), press(HP, 100)])
    assert attempt.directions == "↓ · →"
    # Forward and a heavy punch is still Kyuubi Kudaki, the command normal.
    assert "Hadou Ken" not in attempt.moves


def test_forward_then_down_forward_is_not_a_dragon_punch(play) -> None:
    """The step after the forward wants an exact down, so `f, df` is not a
    shouryuuken however forgiving the game is about entering it."""
    attempt = play([press(FORWARD, 0), press(DOWN, 60), press(HP, 100)])
    assert "Shouryuu Ken" not in attempt.moves


def test_the_second_quarter_circle_may_stop_at_down_forward(play) -> None:
    """`qcf,qcf` is `d, df, f, d, df` in the table: the button lands in place of
    the forward that would have ended it, so the super comes out one direction
    early."""
    script = [
        press(DOWN, 0),
        press(FORWARD, 40),
        release(DOWN, 80),
        release(FORWARD, 120),
        press(DOWN, 140),
        press(FORWARD, 180),  # down-forward, and no plain forward after it
        press(HP, 200),
    ]
    attempt = play(script)
    assert attempt.directions == "↓ ↘ → · ↓ ↘"
    assert attempt.moves == ["Shinkuu Hadou Ken"]


def test_holding_forward_first_does_not_cost_the_dragon_punch(play) -> None:
    """`check_26` does not advance until forward is *released*, so the five
    frames it then allows for the down start there. Hold forward as long as you
    like; the trainer used to time those five frames from pressing it."""
    held = [press(FORWARD, 0), release(FORWARD, 300), press(DOWN, 340), press(FORWARD, 400), press(HP, 430)]
    assert "Shouryuu Ken" in play(held).moves


def test_the_down_must_follow_the_release_quickly(play) -> None:
    """Five frames is 83ms, and it is the tightest gap in the game - which is
    what makes a clean dragon punch hard rather than the motion itself."""
    dawdled = [press(FORWARD, 0), release(FORWARD, 40), press(DOWN, 200), press(FORWARD, 260), press(HP, 290)]
    assert "Shouryuu Ken" not in play(dawdled).moves


def test_the_seam_between_a_supers_two_halves_is_wider(play) -> None:
    """Ten frames within a quarter circle, fourteen between the two of them."""
    script = [
        press(DOWN, 0),
        press(FORWARD, 40),
        release(DOWN, 80),
        release(FORWARD, 120),
        press(DOWN, 300),  # 220ms after the forward: too slow for ten frames, inside fourteen
        press(FORWARD, 340),
        press(HP, 370),
    ]
    assert play(script).moves == ["Shinkuu Hadou Ken"]
