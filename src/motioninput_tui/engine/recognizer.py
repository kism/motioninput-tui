"""Turns a stream of inputs into a stream of activated moves."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from .motions import CHARGE_KINDS, MatchContext, MotionKind, matches

if TYPE_CHECKING:
    from collections.abc import Sequence

    from .buffer import InputBuffer
    from .motions import MotionSpec
    from .notation import Button
    from .ruleset import Ruleset

REPEAT_SUPPRESSION_MS = 120
"""Ignore a re-activation of the same move within this long, so one motion does
not fire twice as the buffer decays."""

# Rough stand-in for a real game's move priority table: the fiddlier the input,
# the more it should win when several moves match the same press.
_KIND_PRIORITY: dict[MotionKind, int] = {
    MotionKind.ROTATE_720: 100,
    MotionKind.ROTATE_360: 90,
    MotionKind.QCF_X2: 85,
    MotionKind.QCB_X2: 85,
    MotionKind.HCF_X2: 85,
    MotionKind.HCB_X2: 85,
    MotionKind.QCF_DP: 84,
    MotionKind.QCB_RDP: 84,
    MotionKind.CHARGE_BFBF: 83,
    MotionKind.CHARGE_DB_UF: 83,
    MotionKind.QCF_UF: 70,
    MotionKind.TIGER_KNEE: 68,
    MotionKind.HCF: 65,
    MotionKind.HCB: 65,
    MotionKind.DP: 60,
    MotionKind.RDP: 60,
    MotionKind.CHARGE_BF: 55,
    MotionKind.CHARGE_DU: 55,
    MotionKind.QCF: 50,
    MotionKind.QCB: 50,
    MotionKind.MASH: 40,
    MotionKind.HOLD: 20,
    MotionKind.ANY: 10,
}


@runtime_checkable
class RecognisableMove(Protocol):
    """The bit of a move the engine cares about."""

    @property
    def name(self) -> str:
        """Display name of the move."""

    @property
    def command(self) -> str:
        """The move's command as written in the reference."""

    @property
    def motion(self) -> MotionSpec | None:
        """The input requirement, if the move has a recognisable one."""

    @property
    def category(self) -> str:
        """Rough move type, used for grouping and colour."""


@dataclass(frozen=True, slots=True)
class Activation:
    """A move the engine believes the player just performed."""

    move: RecognisableMove
    at_ms: int
    buttons: frozenset[Button]
    also_matched: tuple[str, ...] = ()

    @property
    def name(self) -> str:
        """The move's name."""
        return self.move.name


def _priority(move: RecognisableMove) -> int:
    if move.motion is None:
        return -1
    base = _KIND_PRIORITY.get(move.motion.kind, 30)
    # A move needing two buttons beats the same motion with one (PP versions).
    return base * 10 + move.motion.buttons.count


@dataclass
class Recognizer:
    """Matches a character's moves against the live input buffer."""

    moves: Sequence[RecognisableMove]
    ruleset: Ruleset
    decay_ms: int = 0
    """How long the input device takes to reveal a release. See `motions.matches`."""
    _last_fired: dict[str, int] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        """Sort once so evaluation order is stable and priority-first."""
        self._ranked = sorted(
            (move for move in self.moves if move.motion is not None),
            key=_priority,
            reverse=True,
        )

    def evaluate(self, buffer: InputBuffer, at_ms: int, pressed: set[Button]) -> Activation | None:
        """Return the winning move for this press, if any."""
        context = MatchContext(self.ruleset, at_ms, frozenset(pressed), self.decay_ms)
        hits = [move for move in self._ranked if move.motion is not None and matches(move.motion, buffer, context)]
        if not hits:
            return None

        winner = hits[0]
        previous = self._last_fired.get(winner.name)
        if previous is not None and at_ms - previous < REPEAT_SUPPRESSION_MS:
            return None
        self._last_fired[winner.name] = at_ms

        # Charge moves consume their charge, so drop the history that fed them.
        if winner.motion is not None and winner.motion.kind in CHARGE_KINDS:
            buffer.set_direction(buffer.current_direction(), at_ms)

        return Activation(
            move=winner,
            at_ms=at_ms,
            buttons=frozenset(pressed),
            also_matched=tuple(move.name for move in hits[1:4]),
        )

    def reset(self) -> None:
        """Forget recent activations."""
        self._last_fired.clear()
