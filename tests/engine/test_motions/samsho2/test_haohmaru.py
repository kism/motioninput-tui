"""Samurai Shodown II, Haohmaru. The same shared scripts, a third panel again.

A and B are the light and medium slash and C and D the two kicks, so the hitbox
key the Street Fighter games call `HP` is a kick here — and unlike SSV Special,
where C is the only kick, this game answers a kick on a quarter circle with
nothing at all.
"""

from tests.engine.test_motions.harness import (
    BACK,
    DOWN,
    DOWN_DOUBLE_TAP_FORWARD_HP,
    FORWARD,
    HALF_CIRCLE_BACK_FORWARD_HP,
    NEO_A,
    NEO_B,
    NEO_C,
    NEO_D,
    QUARTER_CIRCLE_FORWARD_HP,
    Script,
    press,
    release,
)

QUARTER_CIRCLE_FORWARD_SLASH: Script = [
    press(DOWN, 0),
    press(FORWARD, 70),
    release(DOWN, 110),
    press(NEO_A, 150),
]

DRAGON_PUNCH_KICK: Script = [
    press(FORWARD, 0),
    release(FORWARD, 50),
    press(DOWN, 90),
    press(FORWARD, 150),
    release(DOWN, 190),
    press(NEO_C, 200),
]

# The shared half circle into forward, ending on a slash instead of `HP`: his
# POW move takes A, and the directions are what is being shared.
HALF_CIRCLE_BACK_FORWARD_SLASH: Script = [*HALF_CIRCLE_BACK_FORWARD_HP[:-1], press(NEO_A, 240)]


def test_quarter_circle_with_a_slash_is_the_fireball(play) -> None:
    assert play(QUARTER_CIRCLE_FORWARD_SLASH).moves == ["Ougi Senpu Retsu Zan"]


def test_the_shared_quarter_circle_lands_on_a_kick_and_gives_nothing(play) -> None:
    """`HP` is the third attack column, which this panel calls C: the light
    kick, and his quarter circle is a slash move."""
    assert play(QUARTER_CIRCLE_FORWARD_HP).moves == []


def test_forward_down_downforward_with_a_kick_is_the_rising_slash(play) -> None:
    assert play(DRAGON_PUNCH_KICK).moves == ["Ougi Resshin Zan"]


def test_hold_down_double_tap_forward_gives_nothing(play) -> None:
    """SNK has no dragon punch shortcut, so this is nothing here, as in KoF."""
    assert play(DOWN_DOUBLE_TAP_FORWARD_HP).moves == []


def test_a_half_circle_back_into_forward_is_the_pow_move(play) -> None:
    assert play(HALF_CIRCLE_BACK_FORWARD_SLASH).moves == ["Tenha Seikou Zan"]


# The throws. This guide writes them `b or f + B`, one button and a choice of
# the two sides, which is most of what the roster has. The side is held for a
# second first, standing in for walking into range.


def test_forward_and_a_button_is_the_throw(play) -> None:
    assert play([press(FORWARD, 0), press(NEO_B, 1100)]).moves[0] == "Yokonage"


def test_back_and_the_same_button_is_the_same_throw(play) -> None:
    """Either side does: which one you hold decides which way they land, not
    which move you get."""
    assert play([press(BACK, 0), press(NEO_B, 1100)]).moves[0] == "Yokonage"


def test_the_button_on_its_own_is_not_a_throw(play) -> None:
    """The whole reason a throw is not just its button: pressing B with the
    lever at rest is a normal, which this trainer does not read at all."""
    assert play([press(NEO_B, 0)]).moves == []


def test_a_quick_forward_and_the_button_is_not_a_throw(play) -> None:
    assert play([press(FORWARD, 0), press(NEO_B, 60)]).moves == []


def test_down_and_the_button_is_not_a_throw(play) -> None:
    """Nor is any other direction - the guide said back or forward."""
    assert play([press(DOWN, 0), press(NEO_B, 1100)]).moves == []


def test_the_heavy_slash_throw_is_a_different_move(play) -> None:
    assert play([press(FORWARD, 0), press(NEO_D, 1100)]).moves[0] == "Shinkuu Tomoe Nage"
