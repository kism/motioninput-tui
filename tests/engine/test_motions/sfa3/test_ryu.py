"""Alpha 3, Ryu. Same inputs as `sfiii3/test_ryu.py`, stricter game."""

from tests.engine.test_motions.harness import (
    BACK,
    DOWN,
    DOWN_DOUBLE_TAP_FORWARD_HP,
    FORWARD_INTO_HALF_CIRCLE_FORWARD_HP,
    LK,
    QUARTER_CIRCLE_FORWARD_HP,
    press,
    release,
)


def test_quarter_circle_forward_is_a_fireball(play) -> None:
    assert play(QUARTER_CIRCLE_FORWARD_HP).moves == ["Hadou Ken"]


def test_hold_down_double_tap_forward_does_nothing(play) -> None:
    """Alpha 3 wants the down-forward, so the 3rd Strike shortcut gives nothing."""
    assert play(DOWN_DOUBLE_TAP_FORWARD_HP).moves == []


def test_grounded_quarter_circle_back_kick_is_a_hurricane_kick(play) -> None:
    """The Alpha 3 guide's legend spells out that a trailing '(air)' move works
    on the ground too, so 'Tatsumaki Senpuu Kyaku  qcb + K (air)' does here."""
    script = [
        press(DOWN, 0),
        press(BACK, 60),
        release(DOWN, 110),
        press(LK, 150),
        release(LK, 190),
    ]
    assert play(script).moves == ["Tatsumaki Senpuu Kyaku"]


def test_the_snk_forward_into_half_circle_is_only_the_half_circle_here(play) -> None:
    """`f,b,db,d,df,f` is Ryo's Haoh Shou Ko Ken in KoF '98. Alpha 3 has no move
    on the leading forward, so the roll is only the half circle it ends in."""
    assert play(FORWARD_INTO_HALF_CIRCLE_FORWARD_HP).moves == ["Shakunetsu Hadou Ken"]
