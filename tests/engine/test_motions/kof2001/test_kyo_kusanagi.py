"""KoF 2001, Kyo. The shared scripts, on a Neo Geo panel.

`HP` is the hitbox key that the Neo Geo panel labels C, so the quarter circle
lands on his `236+C` rather than the `236+A` version.

Compare `sfiii3/test_ryu.py`, which gives a dragon punch for the same double
tap. SNK has never had that shortcut, so here it gives nothing at all.
"""

from tests.engine.test_motions.harness import (
    DOWN_DOUBLE_TAP_FORWARD_HP,
    QUARTER_BACK_INTO_HALF_FORWARD_HP,
    QUARTER_CIRCLE_FORWARD_HP,
)


def test_quarter_circle_forward_is_the_heavy_fireball(play) -> None:
    assert play(QUARTER_CIRCLE_FORWARD_HP).moves == ["115 Shiki: Dokugami"]


def test_hold_down_double_tap_forward_gives_nothing(play) -> None:
    """No dragon punch shortcut in KoF, so `d, f, f` is not an Oniyaki."""
    assert play(DOWN_DOUBLE_TAP_FORWARD_HP).moves == []


def test_a_quarter_circle_back_rolled_into_a_half_circle_forward_is_orochi_nagi(play) -> None:
    """`2141236+P`. Iori has no move on this input, so the same script gives him
    a plain fireball off its tail."""
    assert play(QUARTER_BACK_INTO_HALF_FORWARD_HP).moves == ["URA 108 SHIKI: OROCHI NAGI"]
