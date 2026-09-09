"""KoF 2001, Iori. Chained inputs are listed but cannot come out.

The guide writes a rekka as one line with the repeats joined by ``_``, its
"additional input" marker: Aoi Hana is ``214+P_214+P_214+P``. The trainer has no
model for a chain, so the whole move stays in the list struck through rather
than being quietly reduced to its first quarter circle.
"""

from tests.engine.test_motions.harness import (
    HALF_CIRCLE_BACK_FORWARD_HP,
    QUARTER_CIRCLE_FORWARD_HP,
    QUARTER_FORWARD_INTO_HALF_BACK_HP,
)


def test_quarter_circle_forward_is_the_fireball(play) -> None:
    assert play(QUARTER_CIRCLE_FORWARD_HP).moves == ["108 Shiki: Yami Barai"]


def test_a_chained_input_is_listed_but_not_trainable(play) -> None:
    moves = {move.name: move for move in play([]).session.character.moves}

    assert not moves["127 Shiki: Aoi Hana"].trainable, "a rekka chain is not one motion"
    assert not moves["Geshiki: Yumebiki"].trainable, "nor is a repeated command normal"
    # The plain motions either side of them are unaffected.
    assert moves["108 Shiki: Yami Barai"].trainable
    assert moves["212 Shiki: Kototsuki In"].trainable


def test_the_same_roll_as_98_is_still_ya_otome(play) -> None:
    """The guide is numpad here, so `2363214+P` rather than '98's `qcf,hcb + P`.
    Both spell one motion sharing its forward, and take the same input."""
    assert play(QUARTER_FORWARD_INTO_HALF_BACK_HP).moves == ["Kin 1121 Shiki: Ya Otome"]


def test_a_half_circle_back_into_forward_is_kuzukaze(play) -> None:
    assert play(HALF_CIRCLE_BACK_FORWARD_HP).moves == ["Kuzukaze"]
