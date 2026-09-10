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


def test_the_snk_forward_into_half_circle_is_only_a_fireball_here(play) -> None:
    """`f,b,db,d,df,f` is Ryo's Haoh Shou Ko Ken in KoF '98 and nothing in
    Alpha 3, which reads the end of the roll as a plain quarter circle. In 3rd
    Strike the very same script is a dragon punch, since that game will take
    the `d,f` at the end of it as one."""
    assert play(FORWARD_INTO_HALF_CIRCLE_FORWARD_HP).moves == ["Hadou Ken"]
