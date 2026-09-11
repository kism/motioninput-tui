"""Turns a stream of inputs into a stream of activated moves."""

from collections import deque
from dataclasses import dataclass, field, replace
from enum import StrEnum
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from .motions import CHARGE_KINDS, MatchContext, MotionKind, matches

if TYPE_CHECKING:
    from collections.abc import Sequence

    from .buffer import DirectionState, InputBuffer
    from .motions import MotionSpec
    from .notation import Button
    from .ruleset import Ruleset

REPEAT_SUPPRESSION_MS = 120
"""Ignore a re-activation of the same move within this long, so one motion does
not fire twice as the buffer decays."""

BUTTON_GRACE_MS = 50
"""How long a press waits for the rest of a multi-button input before it fires
the lesser move on the same motion. Comfortably over
``InputBuffer.simultaneous_ms`` (40) so the last button of a genuine ``KKK`` the
buffer would still coalesce is not fired past."""

RHYTHM_TAP_MIN_GAP_MS = 70
"""A ``tap P,P,P`` follow-through wants deliberate taps: two closer than this
count as one mashed press and do not advance the follow-up."""

RHYTHM_TAP_MAX_GAP_MS = 500
"""...and no longer than this may pass before the follow-up is judged missed.
Each landed tap pushes the deadline out again."""

SUPER_CATEGORY = "super"
"""The move category an activation cinematic applies to, as a plain string
because ``engine`` never imports ``games``. It is ``games.models.Category.SUPER``
by another name, and only supers freeze the screen: a special with a mashable
tail is read the moment it comes out. See ``Ruleset.super_freeze_ms``."""

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
    MotionKind.QCF_HCB: 84,
    MotionKind.QCB_HCF: 84,
    MotionKind.QCB_DB_F: 84,
    MotionKind.F_HCF: 84,
    MotionKind.CHARGE_BFBF: 83,
    MotionKind.CHARGE_DB_UF: 83,
    MotionKind.HCB_F: 70,
    MotionKind.TIGER_KNEE: 68,
    MotionKind.HCF: 65,
    MotionKind.HCB: 65,
    MotionKind.DP: 60,
    MotionKind.RDP: 60,
    MotionKind.CHARGE_DB_F: 56,
    MotionKind.CHARGE_BF: 55,
    MotionKind.CHARGE_DU: 55,
    MotionKind.F_DF_D: 55,
    MotionKind.B_DB_D: 55,
    MotionKind.QCF: 50,
    MotionKind.QCB: 50,
    MotionKind.MASH: 40,
    MotionKind.HOLD: 20,
    MotionKind.ANY: 10,
}


NOT_MOTIONS = frozenset({MotionKind.ANY, MotionKind.HOLD, MotionKind.MASH})
"""Kinds with no stick motion to watch: a bare button, a held direction, a mash."""


@dataclass(frozen=True, slots=True)
class LiveMotion:
    """A motion a press right now would complete, and the inputs that made it."""

    kind: MotionKind
    start_ms: int
    """When the first direction it used was reached."""
    end_ms: int
    """When the last direction it used was reached."""


def _span(spec: MotionSpec, buffer: InputBuffer, context: MatchContext) -> tuple[int, int]:
    """When the first and last directions a matching motion used were reached.

    The matchers only say whether a motion is there, so this asks again of
    shorter histories: the latest state it can still start from, then the
    earliest it can already finish on. Only call it on a motion that matches.
    """
    states = list(buffer.directions)

    def still_matches(chosen: list[DirectionState]) -> bool:
        return matches(spec, replace(buffer, directions=deque(chosen)), context)

    first = next(k for k in reversed(range(len(states))) if still_matches(states[k:]))
    last = next(e for e in range(first, len(states)) if still_matches(states[first : e + 1]))
    return states[first].start_ms, states[last].start_ms


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


class FollowUpStatus(StrEnum):
    """Where the follow-through of a two-phase move stands."""

    PENDING = "pending"
    """The motion landed; the taps/mash are still expected."""
    COMPLETE = "complete"
    MISSED = "missed"
    """The player stopped, or moved on, before finishing the follow-through."""


@dataclass(slots=True)
class FollowUp:
    """The second phase of a move: a mash or a run of deliberate taps.

    Mutable, and the same object is held by both the :class:`Activation` in the
    feed and :attr:`Recognizer._pending_follow_up`, so the recogniser advancing
    it shows up in the feed on the next repaint.
    """

    button_label: str
    needed: int
    rhythm: bool
    buttons: frozenset[Button]
    deadline_ms: int
    taps_from_ms: int = 0
    """When the activation cinematic ends and the game starts reading again.
    Presses before it are dropped rather than counted or judged missed."""
    frozen: bool = False
    """Whether that cinematic is still running, so the feed can say to wait
    instead of telling the player to mash at a game that is not listening."""
    got: int = 0
    last_tap_ms: int = 0
    status: FollowUpStatus = FollowUpStatus.PENDING


@dataclass(frozen=True, slots=True)
class Activation:
    """A move the engine believes the player just performed."""

    move: RecognisableMove
    at_ms: int
    buttons: frozenset[Button]
    also_matched: tuple[str, ...] = ()
    follow_up: FollowUp | None = None

    @property
    def name(self) -> str:
        """The move's name."""
        return self.move.name


@dataclass(frozen=True, slots=True)
class _Deferred:
    """A press held back to see whether more of a multi-button input arrives."""

    since_ms: int
    pressed: frozenset[Button]


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
    _deferred: _Deferred | None = field(default=None, init=False)
    _pending_follow_up: FollowUp | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        """Sort once so evaluation order is stable and priority-first."""
        self._ranked = sorted(
            (move for move in self.moves if move.motion is not None),
            key=_priority,
            reverse=True,
        )

    def poll(self, buffer: InputBuffer, at_ms: int) -> Activation | None:
        """Fire a press that was held for more buttons and did not get them.

        Called from the session tick. Once the grace window has passed with no
        further button, the lesser move on the motion is allowed through.
        """
        if self._deferred is None or at_ms - self._deferred.since_ms < BUTTON_GRACE_MS:
            return None
        held = self._deferred
        self._deferred = None
        return self.decide(buffer, held.since_ms, held.pressed, allow_defer=False)

    def live_motions(self, buffer: InputBuffer, at_ms: int) -> list[LiveMotion]:
        """The motions a press right now would complete, strongest first.

        Every button counts as down, so this reads the stick alone, and one of
        a motion's moves matching is enough to list it. The moves are already
        ranked, so the first match of each kind comes out in priority order:
        the head of the list is what a press would give, and the rest are what
        it would beat. Each carries when the inputs that made it began and
        ended, so it can be laid over them.
        """
        loose = self.policy is BufferPolicy.LOOSE
        found: list[LiveMotion] = []
        for move in self._ranked:
            spec = move.motion
            if spec is None or spec.kind in NOT_MOTIONS or any(live.kind is spec.kind for live in found):
                continue
            context = MatchContext(self.ruleset, at_ms, spec.buttons.allowed, self.decay_ms, loose=loose)
            if matches(spec, buffer, context):
                found.append(LiveMotion(spec.kind, *_span(spec, buffer, context)))
        return found

    def advance_follow_up(self, at_ms: int) -> bool:
        """Move a pending follow-through's clock on. Driven from the session
        tick; returns True when the feed needs a repaint.

        Two things happen on the clock rather than on a press: the activation
        cinematic ends, and the window to finish the taps runs out.
        """
        pending = self._pending_follow_up
        if pending is None:
            return False
        if pending.frozen and at_ms >= pending.taps_from_ms:
            pending.frozen = False
            return True
        if at_ms < pending.deadline_ms:
            return False
        pending.status = FollowUpStatus.MISSED
        self._pending_follow_up = None
        return True

    def decide(
        self, buffer: InputBuffer, at_ms: int, pressed: frozenset[Button], *, allow_defer: bool = True
    ) -> Activation | None:
        """Return the winning move for this press, if any."""
        # A move mid follow-through owns the press if it is one of that move's
        # taps; anything else abandons the follow-through and is handled below.
        if self._pending_follow_up is not None and self._feed_follow_up(
            buffer, self._pending_follow_up, pressed, at_ms
        ):
            return None

        context = MatchContext(self.ruleset, at_ms, pressed, self.decay_ms, loose=self.policy is BufferPolicy.LOOSE)
        hits = [move for move in self._ranked if move.motion is not None and matches(move.motion, buffer, context)]

        # A move on this same motion that wants more buttons than are down yet:
        # the rest of a KKK lands a few ms later, and firing the one-button move
        # now would spend the buffer first. Held to the next tick rather than
        # re-checked here, since no press comes between.
        if allow_defer and self._awaiting_buttons(buffer, context, hits):
            since = self._deferred.since_ms if self._deferred else at_ms
            self._deferred = _Deferred(since_ms=since, pressed=pressed)
            return None
        self._deferred = None
        if not hits:
            return None

        winner = hits[0]
        previous = self._last_fired.get(winner.name)
        if previous is not None and at_ms - previous < REPEAT_SUPPRESSION_MS:
            return None
        self._last_fired[winner.name] = at_ms

        self._spend(buffer, winner, at_ms)

        spec = winner.motion
        follow_up = self._begin_follow_up(winner, spec, at_ms) if spec is not None and spec.mash else None
        return Activation(
            move=winner,
            at_ms=at_ms,
            buttons=pressed,
            also_matched=tuple(move.name for move in hits[1:4]),
            follow_up=follow_up,
        )

    @property
    def _tap_gap_ms(self) -> int:
        """How long a follow-through waits between taps.

        Zero means the game keeps this the same as the window it counts a mash
        move's opening presses over, which is how the two were one number
        before the pair were told apart.
        """
        return self.ruleset.mash_tap_gap_ms or self.ruleset.mash_window_ms

    def _begin_follow_up(self, move: RecognisableMove, spec: MotionSpec, at_ms: int) -> FollowUp:
        """Open the second phase of a move: expect its taps or its mash.

        A super freezes the screen first, so the whole second phase starts from
        the end of the cinematic rather than from the press that began it -
        including the gap the rhythm variant wants between deliberate taps.
        """
        window = RHYTHM_TAP_MAX_GAP_MS if spec.mash_rhythm else self._tap_gap_ms
        freeze = self.ruleset.super_freeze_ms if move.category == SUPER_CATEGORY else 0
        taps_from = at_ms + freeze
        follow_up = FollowUp(
            button_label=spec.follow_up_label,
            needed=spec.mash,
            rhythm=spec.mash_rhythm,
            buttons=spec.follow_up_buttons,
            deadline_ms=taps_from + window,
            taps_from_ms=taps_from,
            frozen=freeze > 0,
            last_tap_ms=taps_from,
        )
        self._pending_follow_up = follow_up
        return follow_up

    def _feed_follow_up(self, buffer: InputBuffer, pending: FollowUp, pressed: frozenset[Button], at_ms: int) -> bool:
        """Advance (or end) a pending follow-through. Returns True if the press
        was one of its taps and belongs to nothing else."""
        if at_ms < pending.taps_from_ms:
            # Still inside the activation cinematic, where the game reads
            # nothing at all: the press is swallowed whatever it was, and
            # cannot count towards the taps or be judged as abandoning them.
            return True
        if not pressed & pending.buttons:
            pending.status = FollowUpStatus.MISSED
            self._pending_follow_up = None
            return False
        if pending.rhythm and at_ms - pending.last_tap_ms < RHYTHM_TAP_MIN_GAP_MS:
            return True  # a mashed double-tap: eaten, but it does not count
        pending.got += 1
        pending.last_tap_ms = at_ms
        window = RHYTHM_TAP_MAX_GAP_MS if pending.rhythm else self._tap_gap_ms
        pending.deadline_ms = at_ms + window
        if self.policy is BufferPolicy.CONSUME:
            buffer.consume(at_ms)
        if pending.got >= pending.needed:
            pending.status = FollowUpStatus.COMPLETE
            self._pending_follow_up = None
        return True

    def _awaiting_buttons(self, buffer: InputBuffer, context: MatchContext, hits: list[RecognisableMove]) -> bool:
        """Whether a multi-button move on the just-completed motion is still
        waiting for the rest of its buttons, and outranks what did match.

        Only fires once at least one of its buttons is down, so an unrelated
        press is never held.
        """
        if self.policy is BufferPolicy.LOOSE:
            return False
        best_hit = _priority(hits[0]) if hits else -1
        return any(
            move.motion is not None
            and _priority(move) > best_hit
            and 0 < len(context.pressed & move.motion.buttons.allowed) < move.motion.buttons.count
            and matches(move.motion, buffer, replace(context, pressed=context.pressed | move.motion.buttons.allowed))
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
        self._deferred = None
        self._pending_follow_up = None
