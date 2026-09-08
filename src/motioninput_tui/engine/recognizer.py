"""Turns a stream of inputs into a stream of activated moves."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from .motions import CHARGE_KINDS, MatchContext, MotionKind, mash_satisfied, matches, motion_ready

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

    @property
    def super_art(self) -> str:
        """Which Super Art equips this move, or "" if it is always available."""


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
    # A move needing two buttons beats the same motion with one (PP versions),
    # and one that also needs a mash beats the plain motion (Sean's three
    # identical qcf,qcf supers, only one of which wants you to tap after).
    return base * 10 + move.motion.buttons.count + (1 if move.motion.mash else 0)


class BufferPolicy(StrEnum):
    """What happens to the input buffer once a move comes out."""

    CONSUME = "consume"
    """Flush the buffer, as the games do. Two quarter circles give two
    fireballs rather than a super."""

    LOOSE = "loose"
    """Keep everything, so inputs can feed more than one move. Not how any of
    these games behave, but useful for seeing every motion your inputs contain."""


# Contextual moves. A normal or a throw does not clear a game's command buffer,
# so a quarter circle survives an intervening command normal.
_NON_FLUSHING = frozenset({MotionKind.HOLD, MotionKind.ANY})


@dataclass
class Recognizer:
    """Matches a character's moves against the live input buffer."""

    moves: Sequence[RecognisableMove]
    ruleset: Ruleset
    decay_ms: int = 0
    """How long the input device takes to reveal a release. See `motions.matches`."""
    policy: BufferPolicy = BufferPolicy.CONSUME
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
        context = MatchContext(
            self.ruleset, at_ms, frozenset(pressed), self.decay_ms, loose=self.policy is BufferPolicy.LOOSE
        )
        hits = [move for move in self._ranked if move.motion is not None and matches(move.motion, buffer, context)]

        # A move that is one mash short of activating, and would outrank
        # everything that did match, holds the press: firing a lesser move now
        # would flush the buffer before the player finishes tapping.
        if self._awaiting_mash(buffer, context, hits):
            return None
        if not hits:
            return None

        winner = hits[0]
        previous = self._last_fired.get(winner.name)
        if previous is not None and at_ms - previous < REPEAT_SUPPRESSION_MS:
            return None
        self._last_fired[winner.name] = at_ms

        self._spend(buffer, winner, at_ms)

        return Activation(
            move=winner,
            at_ms=at_ms,
            buttons=frozenset(pressed),
            also_matched=tuple(move.name for move in hits[1:4]),
        )

    def _awaiting_mash(self, buffer: InputBuffer, context: MatchContext, hits: list[RecognisableMove]) -> bool:
        """Whether a mash-tail move is still gathering taps and deserves the press.

        Its motion is complete but its mash is not, and it outranks anything
        that did match. Holding here keeps the buffer intact for the next tap;
        under the loose policy nothing is flushed anyway, so there is no need.
        """
        if self.policy is BufferPolicy.LOOSE:
            return False
        best_hit = _priority(hits[0]) if hits else -1
        return any(
            move.motion is not None
            and move.motion.mash
            and _priority(move) > best_hit
            and motion_ready(move.motion, buffer, context)
            and not mash_satisfied(move.motion, buffer, context)
            for move in self._ranked
        )

    def _spend(self, buffer: InputBuffer, winner: RecognisableMove, at_ms: int) -> None:
        """Take the inputs that produced a move out of circulation."""
        kind = winner.motion.kind if winner.motion is not None else None
        if kind is None or kind in _NON_FLUSHING:
            return
        if self.policy is BufferPolicy.CONSUME:
            buffer.consume(at_ms)
        elif kind in CHARGE_KINDS:
            # Even loose matching has to spend a charge, or one held direction
            # would let every charge move fire over and over.
            buffer.set_direction(buffer.current_direction(), at_ms)

    def reset(self) -> None:
        """Forget recent activations."""
        self._last_fired.clear()
