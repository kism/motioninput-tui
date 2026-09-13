"""Samurai Shodown II, Galford. Three rolls of six directions that are not each other.

`f,df,d,db,b` is the Rear Replica Attack and the same roll with a forward on the
end is Mega Strike Heads, so the two lengths have to stay apart. The first also
wants three buttons at once, which is how this guide writes a chord: `BCD`.

Shadow Copy is `f,b,db,d,df,f`, the same six directions as Mega Strike Heads in
very nearly the same order - the brief for this guide had the two down as too
alike to tell apart, and they are what the second motion was added to separate.
"""

from tests.engine.test_motions.harness import (
    FORWARD_INTO_HALF_CIRCLE_FORWARD_HP,
    HALF_CIRCLE_BACK_FORWARD_HP,
    NEO_A,
    NEO_B,
    NEO_C,
    NEO_D,
    Script,
    press,
)

# The shared half circle into forward, minus letting go of back for its forward,
# and its button: the directions up to the back are a plain half circle back.
_ROLL = HALF_CIRCLE_BACK_FORWARD_HP[:-3]

HALF_CIRCLE_BACK_CHORD: Script = [*_ROLL, press(NEO_B, 240), press(NEO_C, 248), press(NEO_D, 256)]
HALF_CIRCLE_BACK_FORWARD_KICK: Script = [*HALF_CIRCLE_BACK_FORWARD_HP[:-1], press(NEO_D, 240)]
FORWARD_INTO_HALF_CIRCLE_FORWARD_SLASH: Script = [*FORWARD_INTO_HALF_CIRCLE_FORWARD_HP[:-1], press(NEO_A, 240)]


def test_a_half_circle_back_with_all_three_is_the_replica(play) -> None:
    assert play(HALF_CIRCLE_BACK_CHORD).moves == ["Rear Replica Attack"]


def test_the_same_roll_with_a_forward_on_the_end_is_the_pow_move(play) -> None:
    assert play(HALF_CIRCLE_BACK_FORWARD_KICK).moves == ["Mega Strike Heads"]


def test_a_forward_then_a_half_circle_forward_is_the_shadow_copy(play) -> None:
    assert play(FORWARD_INTO_HALF_CIRCLE_FORWARD_SLASH).moves == ["Shadow Copy"]


def test_the_other_six_direction_roll_is_not_the_shadow_copy(play) -> None:
    """Mega Strike Heads walks the same ring the other way round. Only where the
    extra back sits tells them apart, which is why each needed its own motion."""
    assert "Shadow Copy" not in play(HALF_CIRCLE_BACK_FORWARD_KICK).moves
