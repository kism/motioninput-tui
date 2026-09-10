"""Last Blade 2, Yuki. The shared scripts against a panel with no punches.

`HP` is the third attack column, which this panel calls C: the kick. Her
quarter circle is a slash move, so the shared script that gives a fireball in
every Street Fighter game gives nothing at all here.
"""

from tests.engine.test_motions.harness import (
    BACK,
    DOWN,
    FORWARD,
    NEO_A,
    NEO_B,
    NEO_C,
    QUARTER_BACK_ROLLED_TO_FORWARD_HP,
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

HALF_CIRCLE_FORWARD_KICK: Script = [
    press(BACK, 0),
    press(DOWN, 60),
    release(BACK, 100),
    press(FORWARD, 140),
    release(DOWN, 180),
    press(NEO_C, 220),
]

# The shared roll on B, which is also what her plain quarter circle back takes.
QUARTER_BACK_ROLLED_TO_FORWARD_SLASH: Script = [*QUARTER_BACK_ROLLED_TO_FORWARD_HP[:-1], press(NEO_B, 240)]


def test_quarter_circle_with_a_slash_is_the_hyoujin(play) -> None:
    assert play(QUARTER_CIRCLE_FORWARD_SLASH).moves == ["HyouJin"]


def test_the_shared_quarter_circle_lands_on_the_kick_and_gives_nothing(play) -> None:
    assert play(QUARTER_CIRCLE_FORWARD_HP).moves == []


def test_a_half_circle_forward_with_the_kick_is_the_hyoukyou(play) -> None:
    assert play(HALF_CIRCLE_FORWARD_KICK).moves == ["HyouKyou"]


def test_the_quarter_back_rolled_on_to_forward_is_the_shin_yukishimaki(play) -> None:
    """`d,db,b + B` is the ShunSetsuZan and `d,db,b,db,f + B` the SDM built on
    top of it, so the longer roll has to win the button they share."""
    assert play(QUARTER_BACK_ROLLED_TO_FORWARD_SLASH).moves == ["Shin YukishiMaki (SDM)"]
