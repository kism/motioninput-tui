"""Ultra SF4, Guile. Charge partitioning, and no quarter circle in the kit."""

from tests.engine.test_motions.harness import (
    BACK,
    DOWN,
    FORWARD,
    HK,
    HP,
    QUARTER_CIRCLE_FORWARD_HP,
    UP,
    press,
    release,
)


def test_charge_back_forward_is_a_sonic_boom(play) -> None:
    script = [
        press(BACK, 0),
        release(BACK, 960),
        press(FORWARD, 970),
        press(HP, 990),
        release(HP, 1030),
    ]
    assert play(script).moves == ["Sonic Boom"]


def test_charge_down_up_is_a_flash_kick(play) -> None:
    script = [
        press(DOWN, 0),
        release(DOWN, 960),
        press(UP, 970),
        press(HK, 990),
        release(HK, 1030),
    ]
    assert play(script).moves == ["Flash Kick"]


def test_quarter_circle_forward_is_not_a_special(play) -> None:
    """Guile has no qcf move; the buffered engine gives the f + HP normal, not a fireball."""
    assert play(QUARTER_CIRCLE_FORWARD_HP).moves == ["Spinning Back Knuckle"]
