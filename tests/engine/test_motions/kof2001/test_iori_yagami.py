"""KoF 2001, Iori. The same rolls as '98, under this guide's move names.

Iori is the cross-check that changing guides did not change what the engine
recognises: `sfiii3` and `kof98` drive these same scripts, and the motions they
land on here are the ones '98 gives, only spelled the way Ice Queen Zero writes
them (`Ya Otome` is listed as `Maiden Masher`, `Kuzukaze` as `Scum Gale`).
"""

from tests.engine.test_motions.harness import (
    HALF_CIRCLE_BACK_FORWARD_HP,
    QUARTER_CIRCLE_FORWARD_HP,
    QUARTER_FORWARD_INTO_HALF_BACK_HP,
)


def test_quarter_circle_forward_is_the_fireball(play) -> None:
    assert play(QUARTER_CIRCLE_FORWARD_HP).moves == ["108 Shiki Yami Barai"]


def test_the_same_roll_as_98_is_still_ya_otome(play) -> None:
    """`d, df, f, df, d, db, b + P`, one motion sharing the forward its halves
    meet on. '98 writes it `qcf,hcb + P` and takes the same input."""
    assert play(QUARTER_FORWARD_INTO_HALF_BACK_HP).moves == ["Maiden Masher (DM)"]


def test_a_half_circle_back_into_forward_is_the_command_grab(play) -> None:
    assert play(HALF_CIRCLE_BACK_FORWARD_HP).moves == ["Scum Gale"]


def test_the_super_moves_section_is_what_makes_a_move_a_super(play) -> None:
    """Nothing about `d, df, f, df, d, db, b` says DM; the guide's heading does.

    The grab above is the same length of roll and stays a special, which is the
    distinction the old numpad guide could not express.
    """
    moves = {move.name: move for move in play([]).session.character.moves}

    assert moves["Maiden Masher (DM)"].category == "super"
    assert moves["Scum Gale"].category == "special"
    assert moves["108 Shiki Yami Barai"].category == "special"
