"""Martial Masters, Master Huang. The four-button panel, and the longest chain."""

from motioninput_tui.games.loader import load_game
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


# Chains. Most of this game's move list is strings off a move that connected,
# and Master Huang has the longest one, so the mechanism is exercised here.

CHAIN_MS = 700
"""``Ruleset.chain_window_ms`` for this game, restated so a test that leans on
the figure fails loudly if it moves."""


def _qcb(at_ms: int, key: str) -> list:
    return [press(DOWN, at_ms), press(BACK, at_ms + 60), release(DOWN, at_ms + 100), press(key, at_ms + 140)]


def _qcf(at_ms: int, key: str) -> list:
    return [press(DOWN, at_ms), press(FORWARD, at_ms + 60), release(DOWN, at_ms + 100), press(key, at_ms + 140)]


def _clear(at_ms: int) -> list:
    """Let go of everything, so the next motion starts from neutral."""
    return [release(BACK, at_ms), release(FORWARD, at_ms), release(SNES_HK, at_ms), release(SNES_LK, at_ms)]


def test_the_chain_window_is_what_this_game_is_tuned_for() -> None:
    assert load_game("martmast").ruleset.chain_window_ms == CHAIN_MS


def test_the_whole_four_link_string_comes_out(play) -> None:
    """Whirlwind Kick, Heavy Axe, High Kicks, Final Kick. Every link is a motion
    this character already has on its own; it is the one before it that decides
    which of the two you get."""
    script = [
        *_qcb(0, SNES_HK),
        *_clear(200),
        *_qcf(240, SNES_HK),
        *_clear(440),
        *_qcb(480, SNES_HK),
        *_clear(680),
        press(SNES_LK, 720),
    ]
    assert play(script).moves == ["Whirlwind Kick", "Heavy Axe", "High Kicks", "Final Kick"]


def test_the_same_quarter_circle_alone_is_the_grasshopper(play) -> None:
    """Heavy Axe is `qcf + K` and so is Grasshopper. With nothing open the plain
    move is what comes out, which is the whole reason a chain link cannot just
    sit in the move list matching whenever its own motion appears."""
    assert play(_qcf(0, SNES_HK)).moves == ["Grasshopper"]


def test_a_link_is_gone_once_the_window_passes(play) -> None:
    """The same two motions with a pause between: the string has closed, so the
    second one is the standalone move again."""
    script = [*_qcb(0, SNES_HK), *_clear(200), *_qcf(200 + CHAIN_MS, SNES_HK)]
    assert play(script).moves == ["Whirlwind Kick", "Grasshopper"]


def test_a_bare_button_on_its_own_is_not_an_input(play) -> None:
    """Final Kick is written `LK` and nothing else. Three links into the string
    that is the move; with nothing open it is a normal the trainer does not
    read, or every move list would be a list of things a button gives you."""
    assert play([press(SNES_LK, 0)]).moves == []


def test_a_move_with_nothing_after_it_closes_the_string(play) -> None:
    """Surge Fist continues nothing, so one done mid-string ends it and the
    quarter circle after is the standalone move again."""
    script = [
        *_qcb(0, SNES_HK),
        *_clear(200),
        *_qcf(240, SNES_LP),
        # Long enough after that the forward the Surge Fist ended on has fallen
        # out of the motion window, or f,d,df would read as a dragon punch.
        *_clear(440),
        *_qcf(800, SNES_HK),
    ]
    assert play(script).moves == ["Whirlwind Kick", "Surge Fist", "Grasshopper"]


def test_the_activation_says_what_it_opened(play) -> None:
    """The feed needs to know, so it can prompt for what is now available."""
    activation = play(_qcb(0, SNES_HK)).session.activations[0]
    assert activation.chain is not None
    assert activation.chain.moves == ("Heavy Axe",)
