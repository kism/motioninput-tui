"""Sailor Moon S, Sailor Mars. A half circle back that carries on down past back."""

from tests.engine.test_motions.harness import (
    BACK,
    DOWN,
    FORWARD,
    SNES_HK,
    press,
    release,
)


def test_a_half_circle_back_carried_on_down_is_the_snake_flare(play) -> None:
    """`f,df,d,db,b,db,d`: round to back as a half circle, then on to down-back
    and down. Her Flame Heel Drop is a plain quarter circle back, which this
    passes clean through on the way, so the longer motion has to win it."""
    script = [
        press(FORWARD, 0),  # f
        press(DOWN, 45),  # df
        release(FORWARD, 90),  # d
        press(BACK, 135),  # db
        release(DOWN, 180),  # b
        press(DOWN, 225),  # db
        release(BACK, 270),  # d
        press(SNES_HK, 310),
    ]
    assert play(script).moves == ["Mars Snake Flare"]


def test_stopping_at_back_is_the_flame_heel_drop(play) -> None:
    """The quarter circle on its own, which is the move it has to be told from."""
    script = [press(DOWN, 0), press(BACK, 60), release(DOWN, 110), press(SNES_HK, 150)]
    assert play(script).moves == ["Flame Heel Drop/Flaming Axe Kick"]


def test_a_half_circle_the_other_way_is_the_snake_fire(play) -> None:
    """Snake Fire is the plain half circle forward; only Snake Flare rolls back."""
    script = [
        press(BACK, 0),
        press(DOWN, 60),
        release(BACK, 100),
        press(FORWARD, 140),
        release(DOWN, 180),
        press(SNES_HK, 220),
    ]
    assert play(script).moves == ["Mars Snake Fire"]
