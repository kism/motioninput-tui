"""Martial Masters, Master Huang. The four-button panel, and no dragon punch shortcut."""

from tests.engine.test_motions.harness import (
    BACK,
    DOWN,
    FORWARD,
    SNES_HK,
    SNES_HP,
    SNES_LK,
    SNES_LP,
    UP,
    press,
    release,
)


def test_quarter_circle_forward_is_the_surge_fist(play) -> None:
    script = [press(DOWN, 0), press(FORWARD, 70), release(DOWN, 110), press(SNES_HP, 150)]
    assert play(script).moves == ["Surge Fist"]


def test_the_same_quarter_circle_on_the_light_punch_is_still_the_surge_fist(play) -> None:
    """`qcf + P` is a choice of two here, not the Street Fighter three."""
    script = [press(DOWN, 0), press(FORWARD, 70), release(DOWN, 110), press(SNES_LP, 150)]
    assert play(script).moves == ["Surge Fist"]


def test_dragon_punch_is_the_nimble_knee(play) -> None:
    script = [
        press(FORWARD, 0),
        release(FORWARD, 60),
        press(DOWN, 60),
        press(FORWARD, 120),
        press(SNES_LK, 170),
    ]
    assert play(script).moves == ["Nimble Knee"]


def test_the_mirrored_dragon_punch_is_the_dragon_kick(play) -> None:
    """`b,d,db + K`, the same shape turned around. Master Huang has both, on the
    same pair of buttons, so only the side the motion runs to tells them apart."""
    script = [
        press(BACK, 0),
        release(BACK, 60),
        press(DOWN, 60),
        press(BACK, 120),
        press(SNES_LK, 170),
    ]
    assert play(script).moves == ["Dragon Kick"]


def test_hold_down_double_tap_forward_does_nothing(play) -> None:
    """The same shape as `DOWN_DOUBLE_TAP_FORWARD_HP`, which is a dragon punch in
    3rd Strike and in USFIV. Written out rather than shared because that script
    presses `HP`, a key this game's four-button panel leaves unbound."""
    script = [
        press(DOWN, 0),
        press(FORWARD, 80),
        release(FORWARD, 150),
        press(FORWARD, 230),
        press(SNES_HP, 270),
    ]
    assert play(script).moves == []


def test_double_quarter_circle_forward_is_the_super(play) -> None:
    script = [
        press(DOWN, 0),
        press(FORWARD, 60),
        release(DOWN, 100),
        release(FORWARD, 140),
        press(DOWN, 180),
        press(FORWARD, 240),
        release(DOWN, 280),
        press(SNES_HP, 320),
    ]
    assert play(script).moves[-1] == "Awakening Spirit"


def test_the_shadow_move_wants_both_of_its_buttons(play) -> None:
    """`qcf + LK+HP`, the meter special every character in the game shares. The
    same quarter circle on either button alone is a different move."""
    circle = [press(DOWN, 0), press(FORWARD, 70), release(DOWN, 110)]
    both = play([*circle, press(SNES_LK, 150), press(SNES_HP, 158)])
    assert both.moves[-1] == "Nimble Whirlwind"
    assert play([*circle, press(SNES_LK, 150)]).moves == ["Grasshopper"]


def test_up_and_the_light_punch_is_the_open_fan(play) -> None:
    assert play([press(UP, 0), press(SNES_LP, 60)]).moves == ["Open Fan"]


def test_the_half_circle_back_is_the_turnover(play) -> None:
    script = [
        press(FORWARD, 0),
        press(DOWN, 40),
        release(FORWARD, 80),
        press(BACK, 120),
        release(DOWN, 160),
        press(SNES_HP, 200),
    ]
    assert play(script).moves == ["Turnover"]


def test_the_quarter_circle_back_is_the_whirlwind_kick(play) -> None:
    script = [press(DOWN, 0), press(BACK, 70), release(DOWN, 110), press(SNES_HK, 150)]
    assert play(script).moves == ["Whirlwind Kick"]
