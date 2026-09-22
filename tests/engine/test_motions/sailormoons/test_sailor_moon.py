"""Sailor Moon S, Sailor Moon. The two-second charge, and no dragon punch shortcut."""

from tests.engine.test_motions.harness import (
    BACK,
    DOWN,
    FORWARD,
    SNES_HK,
    SNES_HP,
    UP,
    press,
    release,
)


def test_quarter_circle_forward_is_the_tiara(play) -> None:
    script = [press(DOWN, 0), press(FORWARD, 70), release(DOWN, 110), press(SNES_HP, 150)]
    assert play(script).moves == ["Moon Tiara Action"]


def test_quarter_circle_back_is_the_spiral_heart(play) -> None:
    script = [press(DOWN, 0), press(BACK, 70), release(DOWN, 110), press(SNES_HP, 150)]
    assert play(script).moves == ["Moon Spiral Heart Attack"]


def test_hold_down_double_tap_forward_does_nothing(play) -> None:
    """The same shape as `DOWN_DOUBLE_TAP_FORWARD_HP`, which is a dragon punch in
    3rd Strike. Written out rather than shared because that script presses `HP`,
    a key this game's four-button panel leaves unbound."""
    script = [
        press(DOWN, 0),
        press(FORWARD, 80),
        release(FORWARD, 150),
        press(FORWARD, 230),
        press(SNES_HP, 270),
    ]
    assert play(script).moves == []


def test_two_seconds_of_down_then_up_is_the_sonic_scream(play) -> None:
    script = [press(DOWN, 0), release(DOWN, 2100), press(UP, 2100), press(SNES_HP, 2150)]
    assert play(script).moves == ["Sonic Scream"]


def test_a_second_of_down_is_not_long_enough_to_charge(play) -> None:
    """A full second charges every other game in the trainer; the guide says this
    one wants two, so the same hold gives nothing here."""
    script = [press(DOWN, 0), release(DOWN, 1000), press(UP, 1000), press(SNES_HP, 1050)]
    assert play(script).moves == []


def test_forward_and_strong_punch_is_the_head_butts(play) -> None:
    assert play([press(FORWARD, 0), press(SNES_HP, 60)]).moves == ["Head Butts"]


def test_quarter_circle_forward_into_a_half_circle_back_is_the_desperation(play) -> None:
    """`d,df,f,df,d,db,b` rolled in one go, the forward shared by both halves."""
    script = [
        press(DOWN, 0),
        press(FORWARD, 45),
        release(DOWN, 90),
        press(DOWN, 135),
        release(FORWARD, 180),
        press(BACK, 225),
        release(DOWN, 270),
        press(SNES_HK, 310),
    ]
    assert play(script).moves == ["Ginguishou"]
