"""``lenient_diagonals``: whether a game lets a motion's diagonal be left out."""

import pytest

from motioninput_tui.engine.buffer import InputBuffer
from motioninput_tui.engine.motions import MatchContext, MotionKind, MotionSpec, matches
from motioninput_tui.engine.notation import ANY_PUNCH, Button, Direction
from motioninput_tui.games.rulesets import GAME_SPECS

QCF = MotionSpec(kind=MotionKind.QCF, buttons=ANY_PUNCH)


def _quarter_circle(*directions: Direction) -> InputBuffer:
    buffer = InputBuffer()
    for at_ms, direction in enumerate(directions):
        buffer.set_direction(direction, at_ms * 30)
    buffer.press_button(Button.LP, 100)
    return buffer


@pytest.mark.parametrize("spec", GAME_SPECS.values(), ids=GAME_SPECS.keys())
def test_down_forward_is_a_quarter_circle_only_where_diagonals_are_lenient(spec) -> None:
    context = MatchContext(ruleset=spec.ruleset, at_ms=100, pressed=frozenset({Button.LP}))
    assert matches(QCF, _quarter_circle(Direction.DOWN, Direction.FORWARD), context) is spec.ruleset.lenient_diagonals


@pytest.mark.parametrize("spec", GAME_SPECS.values(), ids=GAME_SPECS.keys())
def test_the_full_quarter_circle_lands_everywhere(spec) -> None:
    context = MatchContext(ruleset=spec.ruleset, at_ms=100, pressed=frozenset({Button.LP}))
    assert matches(QCF, _quarter_circle(Direction.DOWN, Direction.DOWN_FORWARD, Direction.FORWARD), context)
