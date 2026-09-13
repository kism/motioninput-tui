"""SSV Special, Haohmaru. The shared scripts on a panel that is not punches.

A B AB are the slashes, C the kick and D the dodge, so the hitbox key the other
games call `HP` is the kick button here and the shared quarter circle lands on
the kick version of his fireball rather than the slash one. That is the point of
running the same script against every game.
"""

from tests.engine.test_motions.harness import (
    DOWN,
    DOWN_DOUBLE_TAP_FORWARD_HP,
    FORWARD,
    NEO_A,
    NEO_C,
    NEO_D,
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

DRAGON_PUNCH_SLASH: Script = [
    press(FORWARD, 0),
    release(FORWARD, 50),
    press(DOWN, 90),
    press(FORWARD, 150),
    release(DOWN, 190),
    press(NEO_A, 200),
]


def test_quarter_circle_with_a_slash_is_the_fireball(play) -> None:
    assert play(QUARTER_CIRCLE_FORWARD_SLASH).moves == ["Ougi Senpuu Retsu Zan"]


def test_the_shared_quarter_circle_lands_on_the_kick_version(play) -> None:
    """`HP` is the third attack column, which this panel calls C: the kick."""
    assert play(QUARTER_CIRCLE_FORWARD_HP).moves == ["Ougi Senpuu Retsu Zan (Fake)"]


def test_forward_down_downforward_is_the_rising_slash(play) -> None:
    assert play(DRAGON_PUNCH_SLASH).moves == ["Ougi Kogetsu Zan"]


def test_hold_down_double_tap_forward_gives_nothing(play) -> None:
    """SNK has no dragon punch shortcut, so this is nothing here, as in KoF."""
    assert play(DOWN_DOUBLE_TAP_FORWARD_HP).moves == []


def test_quarter_circle_with_both_rage_buttons_is_the_super(play) -> None:
    """C alone on this motion is the fake fireball; C and D together is the Rage
    super, which must not be eaten by the fake landing on the first button."""
    script = [
        press(DOWN, 0),
        press(FORWARD, 70),
        release(DOWN, 110),
        press(NEO_C, 150),
        press(NEO_D, 158),
    ]
    assert play(script).moves == ["Hiougi Tenha Fuujin Zan"]
