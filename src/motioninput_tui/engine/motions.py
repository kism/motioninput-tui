"""Motion definitions and the matchers that recognise them in an input buffer.

The matchers are deliberately generic: a :class:`~.ruleset.Ruleset` supplies the
leniency, so the same ``qcf`` matcher is strict in Super Turbo and forgiving in
Third Strike.
"""

from collections import Counter
from dataclasses import dataclass
from enum import Enum, StrEnum, auto
from typing import TYPE_CHECKING, NamedTuple

from .notation import (
    BACK_DIRECTIONS,
    DIRECTION_RING,
    DOWN_DIRECTIONS,
    FORWARD_DIRECTIONS,
    KICKS,
    PUNCHES,
    UP_DIRECTIONS,
    Button,
    ButtonRequirement,
    Direction,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from .buffer import DirectionState, InputBuffer
    from .ruleset import Ruleset

_UNBOUNDED = 10**9
AIR_MEMORY_MS = 1000
"""How long after leaving the ground an 'in air' move still counts."""


class MotionKind(StrEnum):
    """The directional part of a move's command."""

    ANY = "any"
    HOLD = "hold"
    QCF = "qcf"
    QCB = "qcb"
    HCF = "hcf"
    HCB = "hcb"
    DP = "dp"
    RDP = "rdp"
    TIGER_KNEE = "tk"
    QCF_X2 = "qcf_x2"
    QCB_X2 = "qcb_x2"
    HCF_X2 = "hcf_x2"
    HCB_X2 = "hcb_x2"
    QCF_DP = "qcf_dp"
    QCB_RDP = "qcb_rdp"
    QCF_HCB = "qcf_hcb"
    QCB_HCF = "qcb_hcf"
    HCB_F = "hcb_f"
    QCB_DB_F = "qcb_db_f"
    F_HCF = "f_hcf"
    QCF_UF = "qcf_uf"
    CHARGE_BF = "charge_bf"
    CHARGE_DU = "charge_du"
    CHARGE_BFBF = "charge_bfbf"
    CHARGE_DB_UF = "charge_db_uf"
    ROTATE_360 = "rotate_360"
    ROTATE_720 = "rotate_720"
    MASH = "mash"


CHARGE_KINDS = frozenset({MotionKind.CHARGE_BF, MotionKind.CHARGE_DU, MotionKind.CHARGE_BFBF, MotionKind.CHARGE_DB_UF})


@dataclass(frozen=True, slots=True)
class MotionSpec:
    """The full input requirement for a move.

    ``mash`` is a follow-up: after the motion activates, a button has to be
    pressed this many times (0 means none). It is how ``qcf,qcf + P, tap P
    rapidly`` (a rapid mash) and ``f,d,df + K, tap P,P,P`` (deliberate taps,
    ``mash_rhythm``) are modelled - the real motion, then a follow-through the
    recogniser tracks as a second phase. ``mash_button`` is ``"P"`` / ``"K"``
    when the taps are a different button from the motion (Sakura Otoshi is
    ``+ K`` then ``tap P``); empty means the same button.
    """

    kind: MotionKind
    buttons: ButtonRequirement
    hold: Direction | None = None
    air: bool = False
    mash: int = 0
    mash_rhythm: bool = False
    mash_button: str = ""
    notation: str = ""

    @property
    def follow_up_buttons(self) -> frozenset[Button]:
        """Which buttons the mash / tap follow-through accepts."""
        if self.mash_button == "P":
            return PUNCHES
        if self.mash_button == "K":
            return KICKS
        return self.buttons.allowed

    @property
    def follow_up_label(self) -> str:
        """How the follow-through button is written."""
        return self.mash_button or self.buttons.label

    def to_dict(self) -> dict[str, object]:
        """Serialise for the generated game data files."""
        data: dict[str, object] = {"kind": self.kind.value, "buttons": self.buttons.to_dict()}
        if self.hold is not None:
            data["hold"] = int(self.hold)
        if self.air:
            data["air"] = True
        if self.mash:
            data["mash"] = self.mash
        if self.mash_rhythm:
            data["mash_rhythm"] = True
        if self.mash_button:
            data["mash_button"] = self.mash_button
        if self.notation:
            data["notation"] = self.notation
        return data

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> MotionSpec:
        """Rebuild from a generated game data file."""
        hold = raw.get("hold")
        return cls(
            kind=MotionKind(raw["kind"]),
            buttons=ButtonRequirement.from_dict(raw["buttons"]),  # ty: ignore[invalid-argument-type]
            hold=Direction(hold) if hold is not None else None,
            air=bool(raw.get("air")),
            mash=int(raw.get("mash", 0)),  # ty: ignore[invalid-argument-type]
            mash_rhythm=bool(raw.get("mash_rhythm")),
            mash_button=str(raw.get("mash_button", "")),
            notation=str(raw.get("notation", "")),
        )


class Pace(Enum):
    """How long the game waits for a step, and from when.

    A game that times every step alike leaves the wide and tight gaps at zero,
    which means "same as ``step_gap_ms``" and makes the distinction disappear.
    Only a game whose figures are actually known sets them.
    """

    ORDINARY = auto()
    """``step_gap_ms``, timed from arriving at the step before."""

    WIDE = auto()
    """``wide_step_gap_ms``. Half circles and the seam between a doubled
    motion's two halves: fourteen frames rather than ten."""

    AFTER_RELEASE = auto()
    """``tight_step_gap_ms``, timed from *letting go* of the step before rather
    than from arriving at it.

    This is the dragon punch, and both halves matter. A game that waits for
    forward to be *let go* before looking for the down is not being strict about
    how long forward was held - only about what follows it. Taking such a game's
    tight figure without its reference point would make the trainer stricter
    than the game rather than more accurate.
    """


class Step(NamedTuple):
    """One step of a motion: which directions satisfy it, and how it is timed.

    ``pace`` is the gap allowed *before* this step, since that is the transition
    the game budgets - a step's own timer starts when the one before it landed.
    """

    allowed: frozenset[Direction]
    skippable: bool = False
    pace: Pace = Pace.ORDINARY


_D = Direction
_DOWNISH_BACK = frozenset({_D.DOWN, _D.DOWN_BACK})
_DOWNISH_FWD = frozenset({_D.DOWN, _D.DOWN_FORWARD})
_ONLY_DOWN = frozenset({_D.DOWN})
_ONLY_DF = frozenset({_D.DOWN_FORWARD})
_ONLY_DB = frozenset({_D.DOWN_BACK})
_ONLY_F = frozenset({_D.FORWARD})
_ONLY_B = frozenset({_D.BACK})
_ONLY_UF = frozenset({_D.UP_FORWARD})
_FWD_OR_DF = frozenset({_D.FORWARD, _D.DOWN_FORWARD})
_BACK_OR_DB = frozenset({_D.BACK, _D.DOWN_BACK})


def _quarter_forward(ruleset: Ruleset) -> list[Step]:
    return [Step(_DOWNISH_BACK), Step(_ONLY_DF, ruleset.lenient_diagonals), Step(_ONLY_F)]


def _quarter_back(ruleset: Ruleset) -> list[Step]:
    return [Step(_DOWNISH_FWD), Step(_ONLY_DB, ruleset.lenient_diagonals), Step(_ONLY_B)]


def _half_down(ruleset: Ruleset) -> frozenset[Direction]:
    """What counts as the down of a half circle.

    Relaxed, a diagonal will do: pressing forward while back is still held goes
    straight to df, so a hitbox half circle usually never touches down at all.
    Strict, the down has to be hit.
    """
    return DOWN_DIRECTIONS if ruleset.lenient_half_circles else _ONLY_DOWN


def _half_forward(ruleset: Ruleset) -> list[Step]:
    if ruleset.half_circle_three_points:
        return [Step(_ONLY_B), Step(DOWN_DIRECTIONS, pace=Pace.WIDE), Step(_ONLY_F, pace=Pace.WIDE)]
    lenient = ruleset.lenient_diagonals
    down = _half_down(ruleset)
    return [Step(_ONLY_B), Step(_ONLY_DB, lenient), Step(down), Step(_ONLY_DF, lenient), Step(_ONLY_F)]


def _half_back(ruleset: Ruleset) -> list[Step]:
    if ruleset.half_circle_three_points:
        return [Step(_ONLY_F), Step(DOWN_DIRECTIONS, pace=Pace.WIDE), Step(_ONLY_B, pace=Pace.WIDE)]
    lenient = ruleset.lenient_diagonals
    down = _half_down(ruleset)
    return [Step(_ONLY_F), Step(_ONLY_DF, lenient), Step(down), Step(_ONLY_DB, lenient), Step(_ONLY_B)]


def _dragon_punch(ruleset: Ruleset) -> list[Step]:
    return [Step(_ONLY_F), Step(_ONLY_DOWN, skippable=ruleset.dp_skip_down, pace=Pace.AFTER_RELEASE), Step(_ONLY_DF)]


def _reverse_dragon_punch(ruleset: Ruleset) -> list[Step]:
    return [Step(_ONLY_B), Step(_ONLY_DOWN, skippable=ruleset.dp_skip_down, pace=Pace.AFTER_RELEASE), Step(_ONLY_DB)]


def _dragon_punch_double_tap() -> list[Step]:
    """Third Strike's 'hold down, double tap forward' dragon punch.

    The leading down may be skipped, which is not leniency for its own sake:
    down is *held* for the whole shortcut rather than being a step of the
    motion, so timing the sequence from it charges the player for holding it.
    What has to be quick is the two taps and the down between them, and that is
    what the remaining steps measure.
    """
    return [
        Step(_DOWNISH_BACK, skippable=True),
        Step(_FWD_OR_DF),
        Step(_DOWNISH_BACK, pace=Pace.AFTER_RELEASE),
        Step(_FWD_OR_DF),
    ]


def _reverse_dragon_punch_double_tap() -> list[Step]:
    return [
        Step(_DOWNISH_FWD, skippable=True),
        Step(_BACK_OR_DB),
        Step(_DOWNISH_FWD, pace=Pace.AFTER_RELEASE),
        Step(_BACK_OR_DB),
    ]


def _dragon_punch_options(ruleset: Ruleset) -> list[list[Step]]:
    options = [_dragon_punch(ruleset)]
    if ruleset.dp_double_tap:
        options.append(_dragon_punch_double_tap())
    return options


def _reverse_dragon_punch_options(ruleset: Ruleset) -> list[list[Step]]:
    options = [_reverse_dragon_punch(ruleset)]
    if ruleset.dp_double_tap:
        options.append(_reverse_dragon_punch_double_tap())
    return options


def _doubled_tail(steps: list[Step], ruleset: Ruleset) -> list[Step]:
    """The second half of a doubled motion.

    Some games stop it one step short - ``qcf,qcf`` read as ``d, df, f, d, df``
    - because the button lands in place of the direction that would have ended
    it. Where a game does that, the super comes out of a hitbox that never
    reaches the last forward.
    """
    tail = steps[:-1] if ruleset.double_motion_drops_tail else steps
    # The seam gets fourteen frames rather than ten, so the first step of the
    # second half is reached at the wider pace.
    return [tail[0]._replace(pace=Pace.WIDE), *tail[1:]] if tail else tail


_SEQUENCE_BUILDERS: dict[MotionKind, Callable[[Ruleset], list[list[Step]]]] = {
    MotionKind.QCF: lambda rules: [_quarter_forward(rules)],
    MotionKind.QCB: lambda rules: [_quarter_back(rules)],
    MotionKind.HCF: lambda rules: [_half_forward(rules)],
    MotionKind.HCB: lambda rules: [_half_back(rules)],
    MotionKind.DP: _dragon_punch_options,
    MotionKind.RDP: _reverse_dragon_punch_options,
    MotionKind.TIGER_KNEE: lambda _: [
        [Step(_ONLY_DOWN), Step(_ONLY_DF, skippable=True), Step(_ONLY_F, skippable=True), Step(_ONLY_UF)]
    ],
    MotionKind.QCF_X2: lambda rules: [[*_quarter_forward(rules), *_doubled_tail(_quarter_forward(rules), rules)]],
    MotionKind.QCB_X2: lambda rules: [[*_quarter_back(rules), *_doubled_tail(_quarter_back(rules), rules)]],
    MotionKind.HCF_X2: lambda rules: [[*_half_forward(rules), *_doubled_tail(_half_forward(rules), rules)]],
    MotionKind.HCB_X2: lambda rules: [[*_half_back(rules), *_doubled_tail(_half_back(rules), rules)]],
    MotionKind.QCF_DP: lambda rules: [[*_quarter_forward(rules), Step(_ONLY_DOWN), Step(_ONLY_DF)]],
    MotionKind.QCB_RDP: lambda rules: [[*_quarter_back(rules), Step(_ONLY_DOWN), Step(_ONLY_DB)]],
    MotionKind.QCF_UF: lambda rules: [[*_quarter_forward(rules), Step(_ONLY_UF)]],
    # KoF's supers join the two halves on a shared direction: qcf~hcb is
    # d,df,f,df,d,db,b, not d,df,f *then* f,df,d,db,b. Nobody returns to
    # neutral mid-motion, so the second motion's opening step is dropped.
    MotionKind.QCF_HCB: lambda rules: [[*_quarter_forward(rules), *_half_back(rules)[1:]]],
    MotionKind.QCB_HCF: lambda rules: [[*_quarter_back(rules), *_half_forward(rules)[1:]]],
    MotionKind.HCB_F: lambda rules: [[*_half_back(rules), Step(_ONLY_F)]],
    # The two SNK rolls. Neither is shorthand for anything shorter: the db of
    # `d,db,b,db,f` is where the roll turns back on itself and the leading f of
    # `f,b,db,d,df,f` is a real tap before the half circle, so both are
    # required steps. Skipping either would leave a plain quarter or half
    # circle, which is the special these supers sit above in the move list.
    MotionKind.QCB_DB_F: lambda rules: [[*_quarter_back(rules), Step(_ONLY_DB), Step(_ONLY_F)]],
    MotionKind.F_HCF: lambda rules: [[Step(_ONLY_F), *_half_forward(rules)]],
}


def _step_sequences(kind: MotionKind, ruleset: Ruleset) -> list[list[Step]]:
    """Every step sequence that satisfies ``kind``. Any one matching is enough."""
    builder = _SEQUENCE_BUILDERS.get(kind)
    return builder(ruleset) if builder is not None else []


_DOUBLE_MOTIONS = frozenset(
    {
        MotionKind.QCF_X2,
        MotionKind.QCB_X2,
        MotionKind.HCF_X2,
        MotionKind.HCB_X2,
        MotionKind.QCF_DP,
        MotionKind.QCB_RDP,
        MotionKind.QCF_HCB,
        MotionKind.QCB_HCF,
    }
)


@dataclass(frozen=True, slots=True)
class _Limits:
    """How sloppily a motion may be performed.

    Attributes:
        max_skip: Junk direction changes allowed between two steps.
        tail_skip: Direction changes allowed after the final step, since a
            motion is usually finished a moment before the button.
        max_gap_ms: The longest pause between one step and the next. Without
            it, a direction left over from an earlier input can act as the
            opening of a motion made much later: hold forward, wait, then tap
            down and down-forward, and the stale forward turns a fireball into
            a dragon punch.
        wide_gap_ms: The same, for a step marked :attr:`Pace.WIDE`.
        release_gap_ms: The same, for a step marked :attr:`Pace.AFTER_RELEASE`.
        paced: Whether this game is known to time steps at more than one pace.
            For a game that is not, every step falls back to ``max_gap_ms``
            measured the ordinary way, since a pace is a claim about a game and
            there is nothing to base one on.
    """

    max_skip: int
    tail_skip: int = 0
    max_gap_ms: int = _UNBOUNDED
    wide_gap_ms: int = _UNBOUNDED
    release_gap_ms: int = _UNBOUNDED
    paced: bool = False

    def resolve(self, pace: Pace) -> Pace:
        """``pace`` as this game reads it, which is bluntly if it has no figures."""
        return pace if self.paced else Pace.ORDINARY

    def gap_for(self, pace: Pace) -> int:
        """The pause allowed before a step held at ``pace``."""
        match pace:
            case Pace.WIDE:
                return self.wide_gap_ms
            case Pace.AFTER_RELEASE:
                return self.release_gap_ms
            case _:
                return self.max_gap_ms


def _timed_from(state: DirectionState, pace: Pace) -> int:
    """The moment a step's pause is counted from.

    Ordinarily that is arriving at the direction before it. A dragon punch is
    the exception where a game waits for forward to be *released* first: the
    clock starts there, so holding it costs nothing.
    """
    if pace is Pace.AFTER_RELEASE and state.end_ms is not None:
        return state.end_ms
    return state.start_ms


def _find_steps(states: list[DirectionState], steps: list[Step], limits: _Limits) -> int | None:
    """Match ``steps`` against ``states`` backwards from the most recent state.

    Returns the index of the earliest state used, or None if there is no match.
    Where several matches exist the tightest (most recent) one wins, since that
    is the one most likely to fall inside the ruleset's window.
    """
    last = len(steps) - 1
    cache: dict[tuple[int, int, int], int | None] = {}

    def candidates(si: int, pi: int, successor: int) -> list[int]:
        """States that could match ``steps[pi]``, most recent first."""
        allowed = steps[pi].allowed
        skip = limits.tail_skip if pi == last else limits.max_skip
        # The pause being bounded is the one before the *next* step, so it is
        # that step's pace that says how long it may be and from when.
        pace = limits.resolve(steps[pi + 1].pace) if successor >= 0 else Pace.ORDINARY
        gap_ms = limits.gap_for(pace)
        found = []
        for j in range(si, max(-1, si - skip - 1), -1):
            if successor >= 0 and states[successor].start_ms - _timed_from(states[j], pace) > gap_ms:
                break  # Anything earlier is further away still.
            if states[j].direction in allowed:
                found.append(j)
        return found

    def search(si: int, pi: int, successor: int) -> int | None:
        if pi < 0:
            return _UNBOUNDED
        key = (si, pi, successor)
        if key in cache:
            return cache[key]
        best: int | None = search(si, pi - 1, successor) if steps[pi][1] else None
        for j in candidates(si, pi, successor):
            deeper = search(j - 1, pi - 1, j)
            if deeper is not None:
                best = max(best, min(deeper, j)) if best is not None else min(deeper, j)
        cache[key] = best
        return best

    result = search(len(states) - 1, last, -1)
    return None if result == _UNBOUNDED else result


def _limits(context: MatchContext) -> _Limits:
    """Leniency for this ruleset, widened by whatever the input device costs."""
    ruleset = context.ruleset

    def gap(configured: int) -> int:
        # Zero means the game does not distinguish this pace from the ordinary one.
        return _UNBOUNDED if context.loose else (configured or ruleset.step_gap_ms) + context.decay_ms

    return _Limits(
        max_skip=ruleset.max_intermediate,
        tail_skip=ruleset.tail_states,
        max_gap_ms=gap(ruleset.step_gap_ms),
        wide_gap_ms=gap(ruleset.wide_step_gap_ms),
        release_gap_ms=gap(ruleset.tight_step_gap_ms),
        paced=bool(ruleset.wide_step_gap_ms or ruleset.tight_step_gap_ms),
    )


def _window_for(kind: MotionKind, ruleset: Ruleset) -> int:
    base = ruleset.motion_window_ms
    return base * 2 if kind in _DOUBLE_MOTIONS else base


def _match_directional(kind: MotionKind, buffer: InputBuffer, context: MatchContext) -> bool:
    ruleset, at_ms, decay_ms = context.ruleset, context.at_ms, context.decay_ms
    window = _window_for(kind, ruleset)
    sequences = _step_sequences(kind, ruleset)
    longest = max((len(steps) for steps in sequences), default=0)
    horizon = at_ms - window - ruleset.activation_window_ms - decay_ms * longest
    states = buffer.directions_since(horizon)
    if not states:
        return False
    for steps in sequences:
        earliest = _find_steps(states, steps, _limits(context))
        if earliest is None:
            continue
        # Each step of the motion costs one decay window, because a keyboard
        # only reveals that a direction was let go once its hold lapses.
        allowance = window + ruleset.activation_window_ms + decay_ms * max(0, len(steps) - 1)
        if at_ms - states[earliest].start_ms <= allowance:
            return True
    return False


_CHARGE_DEFINITIONS: dict[MotionKind, tuple[frozenset[Direction], list[Step]]] = {
    MotionKind.CHARGE_BF: (BACK_DIRECTIONS, [Step(FORWARD_DIRECTIONS)]),
    MotionKind.CHARGE_DU: (DOWN_DIRECTIONS, [Step(UP_DIRECTIONS)]),
    MotionKind.CHARGE_BFBF: (
        BACK_DIRECTIONS,
        [Step(FORWARD_DIRECTIONS), Step(BACK_DIRECTIONS), Step(FORWARD_DIRECTIONS)],
    ),
    MotionKind.CHARGE_DB_UF: (
        frozenset({_D.DOWN_BACK, _D.DOWN}),
        [Step(_ONLY_DF), Step(_ONLY_DB), Step(frozenset({_D.UP_FORWARD, _D.UP}))],
    ),
}


def _charged_by(
    states: list[DirectionState],
    index: int,
    charge_dirs: frozenset[Direction],
    ruleset: Ruleset,
    at_ms: int,
) -> bool:
    """Whether the charge is full by the time ``states[index]`` is let go.

    Ordinarily the hold has to be unbroken, which is what ``charge_reset_ms`` of
    zero means. A game may instead let it **accumulate**, never giving back what
    has been counted so far and starting over only once the player has spent
    ``charge_reset_ms`` off the direction, added up. Charge for a third of a
    second, let go for a third, charge for a third more, and it is ready.
    """
    reset_ms = ruleset.charge_reset_ms
    if not reset_ms:
        return states[index].duration_ms(at_ms) >= ruleset.charge_ms
    held_ms = idle_ms = 0
    for state in reversed(states[: index + 1]):
        duration = state.duration_ms(at_ms)
        if state.direction in charge_dirs:
            held_ms += duration
            if held_ms >= ruleset.charge_ms:
                return True
        else:
            idle_ms += duration
            if idle_ms > reset_ms:
                return False
    return False


def _match_charge(kind: MotionKind, buffer: InputBuffer, context: MatchContext) -> bool:
    ruleset, at_ms, decay_ms = context.ruleset, context.at_ms, context.decay_ms
    charge_dirs, release_steps = _CHARGE_DEFINITIONS[kind]
    states = list(buffer.directions)
    release_budget = ruleset.charge_release_ms + (ruleset.motion_window_ms + decay_ms) * len(release_steps)
    for index in range(len(states) - 1, -1, -1):
        state = states[index]
        if state.direction not in charge_dirs:
            continue
        if state.end_ms is None or at_ms - state.end_ms > release_budget:
            continue
        if not _charged_by(states, index, charge_dirs, ruleset, at_ms):
            continue
        if _find_steps(states[index + 1 :], release_steps, _limits(context)) is not None:
            return True
    return False


def _ring_index(direction: Direction) -> int | None:
    try:
        return DIRECTION_RING.index(direction)
    except ValueError:
        return None


_CARDINALS = frozenset({_D.UP, _D.DOWN, _D.FORWARD, _D.BACK})


def _match_rotation_cardinals(turns: int, buffer: InputBuffer, ruleset: Ruleset, at_ms: int) -> bool:
    """Detect ``turns`` full circles by collecting cardinals.

    A game reading a rotation this way keeps a four bit set of which cardinals
    have been seen, compares the lever for **equality** so that no diagonal ever
    counts towards one, and does not care what order they arrive in. Two timers
    wipe that set: ``rotation_cardinal_gap_ms`` without the lever resting on a
    cardinal, and ``rotation_window_ms`` for the turn. A neutral is not special
    - it only costs the time it takes.

    So four separate taps of up, down, forward and back really are a 360 here,
    and rolling a stick round the gate is one because it passes over all four,
    not because of how far it travelled. What makes it hard is the pace, and
    ``jump_grace_ms``: the up the circle cannot do without is also a
    jump, so the button has to arrive while the jump is still starting.

    ponytail: the game's thirty-two frame budget is a free running bucket rather
    than a window opened by the player, so straddling its boundary fails a turn
    that was quick enough. Modelled here as a budget that starts at the first
    cardinal and restarts when it lapses, since the trainer has no frame clock
    to share the game's phase and losing a good 360 to luck teaches nothing.
    """
    window = ruleset.rotation_window_ms
    gap_ms = ruleset.rotation_cardinal_gap_ms
    states = buffer.directions_since(at_ms - window * turns)
    collected: set[Direction] = set()
    turns_done = 0
    opened_ms = 0
    left_cardinal_ms: int | None = None
    for state in states:
        if state.direction not in _CARDINALS:
            continue
        lapsed = left_cardinal_ms is not None and state.start_ms - left_cardinal_ms > gap_ms
        if collected and (lapsed or state.start_ms - opened_ms > window):
            collected = set()
        if not collected:
            opened_ms = state.start_ms
        collected.add(state.direction)
        left_cardinal_ms = state.end_ms if state.end_ms is not None else at_ms
        if collected != _CARDINALS:
            continue
        collected = set()
        if turns_done + 1 < turns:
            turns_done += 1
        elif not _jumped_away(states, opened_ms, ruleset.jump_grace_ms, at_ms):
            return True
    return False


def _jumped_away(states: list[DirectionState], since_ms: int, grace_ms: int, at_ms: int) -> bool:
    """Whether the up this turn needed has already carried the character off the ground.

    Up is a jump input, so a turn that passes through it commits to a jump the
    moment it does, diagonals included - up-back on the way round the gate
    counts. ``grace_ms`` is how long the jump takes to leave the ground; press
    the button inside that and the move still comes out, press it after and the
    game is reading an airborne character and gives nothing.

    ponytail: only the last turn is judged, since the trainer has no airborne
    state to carry and an earlier turn's up is nowhere near ``at_ms`` by the
    time the button lands. A 720 that jumped away on its first revolution is
    taken on trust, which is roughly fair - the way to land one is out of a jump
    or a move's recovery, where the up was never a jump to begin with.
    """
    if not grace_ms:
        return False
    for state in states:
        if state.start_ms >= since_ms and state.direction in UP_DIRECTIONS:
            return at_ms - state.start_ms > grace_ms
    return False


def _match_rotation(turns: int, buffer: InputBuffer, ruleset: Ruleset, at_ms: int) -> bool:
    """Detect ``turns`` full circles.

    Rather than demanding all eight directions, this accumulates how far around
    the ring the stick has travelled without reversing, which is what lets a
    hitbox player get a 360 out of a roll through four keys.

    **Letting go breaks the circle.** A neutral is a state like any other here,
    not a gap to be skipped over: it means every direction came up, which on a
    stick is the hand leaving it. Tapping four cardinals with a full release
    between each is not a 360 in any of these games, and without this it was one
    in all of them - the single reason a 360 landed every time in the trainer
    and hardly ever in the game.

    A game whose rule is known rather than reckoned uses
    :func:`_match_rotation_cardinals` instead.
    """
    if ruleset.rotation_cardinal_gap_ms:
        return _match_rotation_cardinals(turns, buffer, ruleset, at_ms)
    horizon = at_ms - ruleset.rotation_window_ms * turns
    ring = [_ring_index(state.direction) for state in buffer.directions_since(horizon)]
    needed = max(4, 8 * turns - ruleset.rotation_slack * turns)
    for direction in (1, -1):
        travelled = 0
        previous: int | None = None
        for index in ring:
            if index is None:
                travelled = 0  # Neutral: the stick was let go and the circle restarts.
                previous = None
                continue
            if previous is None:
                previous = index
                continue
            delta = ((index - previous) * direction) % 8
            if 0 < delta <= 3:  # ruff: ignore[magic-value-comparison] - skipping up to two ring positions still counts
                travelled += delta
                previous = index
            elif delta != 0:
                travelled = 0
                previous = index
            if travelled >= needed:
                return True
    return False


def _match_hold(hold: Direction | None, buffer: InputBuffer) -> bool:
    if hold is None:
        return True
    current = buffer.current_direction()
    return current in _hold_set(hold)


def _hold_set(hold: Direction) -> frozenset[Direction]:
    """Cardinal holds accept their neighbouring diagonals; diagonals are exact."""
    match hold:
        case Direction.DOWN:
            return DOWN_DIRECTIONS
        case Direction.UP:
            return UP_DIRECTIONS
        case Direction.BACK:
            return frozenset({Direction.BACK})
        case Direction.FORWARD:
            return frozenset({Direction.FORWARD})
        case _:
            return frozenset({hold})


def _match_air(buffer: InputBuffer, at_ms: int) -> bool:
    return any(state.direction in UP_DIRECTIONS for state in buffer.directions_since(at_ms - AIR_MEMORY_MS))


_ROTATIONS = frozenset({MotionKind.ROTATE_360, MotionKind.ROTATE_720})


def _match_ground(spec: MotionSpec, buffer: InputBuffer, ruleset: Ruleset, at_ms: int) -> bool:
    """Whether a move that has to be done standing still can be.

    The counterpart to :func:`_match_air`, and it uses the same memory: an up
    puts the character in the air for :data:`AIR_MEMORY_MS`, which is what lets
    an air move count, and for exactly as long a grounded move cannot. All the
    ground it leaves is ``jump_grace_ms``, the jump's own startup.

    This is why a half circle that overshoots to up-back gives nothing rather
    than the throw it passed through, and why a circle rolled at leisure round
    the top of the gate is a jump. Rotations answer it for themselves, per turn:
    they cannot avoid an up, so only the turn in progress can be held against
    them.
    """
    if not ruleset.jump_grace_ms or spec.kind in _ROTATIONS:
        return True
    horizon = at_ms - AIR_MEMORY_MS
    return not _jumped_away(buffer.directions_since(horizon), horizon, ruleset.jump_grace_ms, at_ms)


def _mash_hits(spec: MotionSpec, buffer: InputBuffer, ruleset: Ruleset, at_ms: int) -> int:
    """How many presses within the mash window count towards the move.

    ponytail: the window slides, where a game may instead wipe its counters on a
    free running cadence the player cannot see. Same trade as the 360 in
    :func:`_match_rotation_cardinals` - a bucket boundary would lose a mash that
    was fast enough, by luck, and teach nothing.
    """
    recent = [
        press for press in buffer.buttons_since(at_ms - ruleset.mash_window_ms) if press.button in spec.buttons.allowed
    ]
    if not ruleset.mash_same_button:
        return len(recent)
    # One counter per button, and the best of them is what fires the move.
    tallies = Counter(press.button for press in recent)
    return max(tallies.values(), default=0)


def _match_mash(spec: MotionSpec, buffer: InputBuffer, ruleset: Ruleset, at_ms: int) -> bool:
    return _mash_hits(spec, buffer, ruleset, at_ms) >= ruleset.mash_count


_SIMPLE_MATCHERS: dict[MotionKind, Callable[[MotionSpec, InputBuffer, Ruleset, int], bool]] = {
    MotionKind.ANY: lambda *_: True,
    MotionKind.HOLD: lambda spec, buffer, _ruleset, _at: _match_hold(spec.hold, buffer),
    MotionKind.MASH: _match_mash,
    MotionKind.ROTATE_360: lambda _spec, buffer, ruleset, at: _match_rotation(1, buffer, ruleset, at),
    MotionKind.ROTATE_720: lambda _spec, buffer, ruleset, at: _match_rotation(2, buffer, ruleset, at),
}


@dataclass(frozen=True, slots=True)
class MatchContext:
    """Everything about the moment a button was pressed.

    ``decay_ms`` is how long the input device takes to reveal that a direction
    was released. It is zero for a device that reports releases, and the hold
    window for a keyboard, where it has to be added to every motion's timing
    budget or nothing but the shortest motions would ever land in time.
    """

    ruleset: Ruleset
    at_ms: int
    pressed: frozenset[Button]
    decay_ms: int = 0
    loose: bool = False
    """Drop the limit on how long a motion may pause between steps, so inputs
    can feed more than one move. Not how the games behave."""


def matches(spec: MotionSpec, buffer: InputBuffer, context: MatchContext) -> bool:
    """Whether the motion, buttons and air requirement are all met right now.

    A ``mash`` tail is *not* a gate: the motion activates on its own and the
    recogniser tracks the follow-through as a second phase. Standalone
    :attr:`MotionKind.MASH` moves have no ``mash`` tail and are still gated by
    :func:`_match_mash` inside :func:`_match_kind`.
    """
    if len(context.pressed & spec.buttons.allowed) < spec.buttons.count:
        return False
    if spec.air:
        if not _match_air(buffer, context.at_ms):
            return False
    elif not _match_ground(spec, buffer, context.ruleset, context.at_ms):
        return False
    return _match_kind(spec, buffer, context)


def _match_kind(spec: MotionSpec, buffer: InputBuffer, context: MatchContext) -> bool:
    """The directional / charge / rotation / hold part of the requirement."""
    simple = _SIMPLE_MATCHERS.get(spec.kind)
    if simple is not None:
        return simple(spec, buffer, context.ruleset, context.at_ms)
    if spec.kind in CHARGE_KINDS:
        return _match_charge(spec.kind, buffer, context)
    return _match_directional(spec.kind, buffer, context)
