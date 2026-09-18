"""Sailor Moon S, Sailor Uranus. Out to back and all the way home again."""

from tests.engine.test_motions.harness import (
    BACK,
    DOWN,
    FORWARD,
    SNES_HK,
    SNES_LP,
    press,
    release,
)


def test_a_half_circle_each_way_is_the_destructive_carnival(play) -> None:
    """`f,df,d,db,b,db,d,df,f`: a half circle back, then a half circle forward
    off the back they share. Nine directions, which only fits because a compound
    motion is allowed twice the window of a plain one."""
    script = [
        press(FORWARD, 0),  # f
        press(DOWN, 40),  # df
        release(FORWARD, 80),  # d
        press(BACK, 120),  # db
        release(DOWN, 160),  # b
        press(DOWN, 200),  # db
        release(BACK, 240),  # d
        press(FORWARD, 280),  # df
        release(DOWN, 320),  # f
        press(SNES_HK, 360),
    ]
    assert play(script).moves == ["Destructive Carnival"]


def test_stopping_at_down_is_the_world_shaking(play) -> None:
    """The first three notches of that roll, which is her fireball."""
    script = [press(FORWARD, 0), press(DOWN, 40), release(FORWARD, 80), press(SNES_LP, 120)]
    assert play(script).moves == ["World Shaking"]
