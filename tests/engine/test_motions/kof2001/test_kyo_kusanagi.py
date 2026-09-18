"""KoF 2001, Kyo. The shared scripts, on a Neo Geo panel, plus his rekka chains.

`HP` is the hitbox key that the Neo Geo panel labels C, so the quarter circle
lands on his `d, df, f + C` rather than the `+ A` version.

Compare `sfiii3/test_ryu.py`, which gives a dragon punch for the same double
tap. SNK has never had that shortcut, so here it gives nothing at all.
"""

from tests.engine.test_motions.harness import (
    DOWN,
    DOWN_DOUBLE_TAP_FORWARD_HP,
    FORWARD,
    NEO_A,
    NEO_B,
    QUARTER_BACK_INTO_HALF_FORWARD_HP,
    QUARTER_CIRCLE_FORWARD_HP,
    press,
    release,
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


def test_a_rekka_link_knows_the_move_it_comes_out_of(play) -> None:
    """This guide writes a chain by naming the move it comes out of.

    `128 Shiki Kono Kizu: 114 Shiki Aragami, d, df, f + P` is the head of the
    string, a comma, then this link's own input. The name in front is what
    makes it a chain rather than a second fireball on one motion.
    """
    moves = {move.name: move for move in play([]).session.character.moves}

    assert moves["128 Shiki Kono Kizu"].follows == "114 Shiki Aragami"
    # The move the chain starts from, and the plain motions around it, stand alone.
    assert not moves["114 Shiki Aragami"].follows
    assert moves["115 Shiki Domu Kami"].trainable
    assert moves["R.E.D. Kick"].trainable


def test_the_rekka_link_only_comes_out_after_its_parent(play) -> None:
    """The link is a quarter circle and so is the fireball above it. Which one
    you get is decided by whether the string is open."""
    assert play(QUARTER_CIRCLE_FORWARD_HP).moves == ["115 Shiki Domu Kami"]

    assert play([*_qcf(0, NEO_A), *_clear(200), *_qcf(260, NEO_A)]).moves == [
        "114 Shiki Aragami",
        "128 Shiki Kono Kizu",
    ]


def test_the_string_runs_two_links_deep(play) -> None:
    """Kyo's rekka is a tree: Aragami into Kono Kizu, and out of that either a
    kick or a punch. The last link is a bare button, which is an input only
    because two moves have already opened the way to it."""
    script = [*_qcf(0, NEO_A), *_clear(200), *_qcf(260, NEO_A), *_clear(460), press(NEO_B, 520)]
    assert play(script).moves == ["114 Shiki Aragami", "128 Shiki Kono Kizu", "125 Shiki Nana Se"]


def test_the_bare_button_link_is_nothing_on_its_own(play) -> None:
    """The same press with no string open. A lone kick is a normal, and the
    trainer does not read those."""
    assert play([press(NEO_B, 0)]).moves == []


def _qcf(at_ms: int, key: str) -> list:
    return [press(DOWN, at_ms), press(FORWARD, at_ms + 60), release(DOWN, at_ms + 100), press(key, at_ms + 140)]


def _clear(at_ms: int) -> list:
    """Let go of everything, so the next motion starts from neutral."""
    return [release(FORWARD, at_ms), release(NEO_A, at_ms), release(NEO_B, at_ms)]
