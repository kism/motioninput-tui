"""KoF 2001, Kyo. The shared scripts, on a Neo Geo panel, plus his rekka chains.

`HP` is the hitbox key that the Neo Geo panel labels C, so the quarter circle
lands on his `d, df, f + C` rather than the `+ A` version.

Compare `sfiii3/test_ryu.py`, which gives a dragon punch for the same double
tap. SNK has never had that shortcut, so here it gives nothing at all.
"""

from tests.engine.test_motions.harness import (
    DOWN_DOUBLE_TAP_FORWARD_HP,
    QUARTER_BACK_INTO_HALF_FORWARD_HP,
    QUARTER_CIRCLE_FORWARD_HP,
)


def test_quarter_circle_forward_is_the_heavy_fireball(play) -> None:
    assert play(QUARTER_CIRCLE_FORWARD_HP).moves == ["115 Shiki Domu Kami"]


def test_hold_down_double_tap_forward_gives_nothing(play) -> None:
    """No dragon punch shortcut in KoF, so `d, f, f` is not an Oniyaki."""
    assert play(DOWN_DOUBLE_TAP_FORWARD_HP).moves == []


def test_a_quarter_circle_back_rolled_into_a_half_circle_forward_is_orochi_nagi(play) -> None:
    """`d, db, b, db, d, df, f + P`. Iori has no move on this input, so the same
    script gives him a plain fireball off its tail."""
    assert play(QUARTER_BACK_INTO_HALF_FORWARD_HP).moves == ["Ura 108 Shiki: Orochinagi(DM)"]


def test_a_follow_up_is_listed_but_not_trainable(play) -> None:
    """This guide writes a chain by naming the move it comes out of.

    `128 Shiki Kono Kizu: 114 Shiki Aragami, d, df, f + P` still has a quarter
    circle in it, so it has to be rejected on the prose rather than the motion,
    or Kyo would have two fireballs on one input.
    """
    moves = {move.name: move for move in play([]).session.character.moves}

    assert not moves["128 Shiki Kono Kizu"].trainable, "a rekka link is not a motion of its own"
    assert not moves["402 Shiki Batu Yomi"].trainable, "nor is the link after that one"
    # The move the chain starts from, and the plain motions around it, are unaffected.
    assert moves["114 Shiki Aragami"].trainable
    assert moves["115 Shiki Domu Kami"].trainable
    assert moves["R.E.D. Kick"].trainable
