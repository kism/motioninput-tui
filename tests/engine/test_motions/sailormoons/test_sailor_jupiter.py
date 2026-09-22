"""Sailor Moon S, Sailor Jupiter. The circle, which this guide spells out in full."""

from tests.engine.test_motions.harness import (
    BACK,
    DOWN,
    FORWARD,
    SNES_LP,
    UP,
    press,
    release,
)


def test_a_full_circle_is_the_giant_swing(play) -> None:
    """Right round the gate from forward, a notch at a time, and then a punch."""
    script = [
        press(FORWARD, 0),  # f
        press(DOWN, 50),  # df
        release(FORWARD, 100),  # d
        press(BACK, 150),  # db
        release(DOWN, 200),  # b
        press(UP, 250),  # ub
        release(BACK, 300),  # u
        press(FORWARD, 350),  # uf
        press(SNES_LP, 390),
    ]
    assert play(script).moves == ["Giant Swing"]


def test_stopping_a_third_of_the_way_round_is_the_coconut_cyclone(play) -> None:
    """The first three notches of that same circle, taken on their own. The
    button is what separates them: carry on round and it is too late for this
    move, which is why the circle above does not bring it out on the way past."""
    script = [
        press(FORWARD, 0),
        press(DOWN, 50),
        release(FORWARD, 100),
        press(SNES_LP, 140),
    ]
    assert play(script).moves == ["Jupiter Coconut Cyclone"]
