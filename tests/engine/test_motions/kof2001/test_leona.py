"""KoF 2001, Leona. Charge moves, which none of the shared scripts exercise.

She is the game's charge character: `2.8+P` and `4.6+P` in the guide's numpad,
which is down held then up, and back held then forward. The ruleset asks for
700ms in the held direction, so the short holds below must give nothing.
"""

from tests.engine.test_motions.harness import BACK, DOWN, FORWARD, HP, UP, Script, press, release

LONG_MS = 750
SHORT_MS = 300


def _charge(held: str, released: str, hold_ms: int) -> Script:
    """Hold one direction, let it go, then the opposite way plus a punch."""
    return [
        press(held, 0),
        release(held, hold_ms),
        press(released, hold_ms + 10),
        press(HP, hold_ms + 50),
        release(released, hold_ms + 120),
    ]


def test_charging_down_then_up_is_the_moon_slasher(play) -> None:
    assert play(_charge(DOWN, UP, LONG_MS)).moves == ["Moon Slasher"]


def test_charging_back_then_forward_is_the_vortex_launcher(play) -> None:
    assert play(_charge(BACK, FORWARD, LONG_MS)).moves == ["Vortex Launcher"]


def test_a_short_hold_is_not_a_charge(play) -> None:
    """The direction has to be held, not passed through on the way to the button."""
    assert play(_charge(DOWN, UP, SHORT_MS)).moves == []
    assert play(_charge(BACK, FORWARD, SHORT_MS)).moves == []
