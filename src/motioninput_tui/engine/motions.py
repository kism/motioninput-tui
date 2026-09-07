"""Motion definitions and the matchers that recognise them in an input buffer.

The matchers are deliberately generic: a :class:`~.ruleset.Ruleset` supplies the
leniency, so the same ``qcf`` matcher is strict in Super Turbo and forgiving in
Third Strike.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from .notation import (
    BACK_DIRECTIONS,
    DIRECTION_RING,
    DOWN_DIRECTIONS,
    FORWARD_DIRECTIONS,
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
    """The full input requirement for a move."""

    kind: MotionKind
    buttons: ButtonRequirement
    hold: Direction | None = None
    air: bool = False
    notation: str = ""

    def to_dict(self) -> dict[str, object]:
        """Serialise for the generated game data files."""
        data: dict[str, object] = {"kind": self.kind.value, "buttons": self.buttons.to_dict()}
        if self.hold is not None:
            data["hold"] = int(self.hold)
        if self.air:
            data["air"] = True
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
            notation=str(raw.get("notation", "")),
        )


# A step is a set of acceptable directions plus whether it may be skipped.
Step = tuple[frozenset[Direction], bool]

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
    return [(_DOWNISH_BACK, False), (_ONLY_DF, ruleset.lenient_diagonals), (_ONLY_F, False)]


def _quarter_back(ruleset: Ruleset) -> list[Step]:
    return [(_DOWNISH_FWD, False), (_ONLY_DB, ruleset.lenient_diagonals), (_ONLY_B, False)]


def _half_forward(ruleset: Ruleset) -> list[Step]:
    lenient = ruleset.lenient_diagonals
    return [(_ONLY_B, False), (_ONLY_DB, lenient), (DOWN_DIRECTIONS, False), (_ONLY_DF, lenient), (_ONLY_F, False)]


def _half_back(ruleset: Ruleset) -> list[Step]:
    lenient = ruleset.lenient_diagonals
    return [(_ONLY_F, False), (_ONLY_DF, lenient), (DOWN_DIRECTIONS, False), (_ONLY_DB, lenient), (_ONLY_B, False)]


def _dragon_punch(ruleset: Ruleset) -> list[Step]:
    return [(_ONLY_F, False), (_ONLY_DOWN, ruleset.dp_skip_down), (_ONLY_DF, False)]


def _reverse_dragon_punch(ruleset: Ruleset) -> list[Step]:
    return [(_ONLY_B, False), (_ONLY_DOWN, ruleset.dp_skip_down), (_ONLY_DB, False)]


def _dragon_punch_double_tap() -> list[Step]:
    """Third Strike's 'hold down, double tap forward' dragon punch.

    The leading down may be skipped, which is not leniency for its own sake:
    down is *held* for the whole shortcut rather than being a step of the
    motion, so timing the sequence from it charges the player for holding it.
    What has to be quick is the two taps and the down between them, and that is
    what the remaining steps measure.
    """
    return [(_DOWNISH_BACK, True), (_FWD_OR_DF, False), (_DOWNISH_BACK, False), (_FWD_OR_DF, False)]


def _reverse_dragon_punch_double_tap() -> list[Step]:
    return [(_DOWNISH_FWD, True), (_BACK_OR_DB, False), (_DOWNISH_FWD, False), (_BACK_OR_DB, False)]


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


_SEQUENCE_BUILDERS: dict[MotionKind, Callable[[Ruleset], list[list[Step]]]] = {
    MotionKind.QCF: lambda rules: [_quarter_forward(rules)],
    MotionKind.QCB: lambda rules: [_quarter_back(rules)],
    MotionKind.HCF: lambda rules: [_half_forward(rules)],
    MotionKind.HCB: lambda rules: [_half_back(rules)],
    MotionKind.DP: _dragon_punch_options,
    MotionKind.RDP: _reverse_dragon_punch_options,
    MotionKind.TIGER_KNEE: lambda _: [[(_ONLY_DOWN, False), (_ONLY_DF, True), (_ONLY_F, True), (_ONLY_UF, False)]],
    MotionKind.QCF_X2: lambda rules: [[*_quarter_forward(rules), *_quarter_forward(rules)]],
    MotionKind.QCB_X2: lambda rules: [[*_quarter_back(rules), *_quarter_back(rules)]],
    MotionKind.HCF_X2: lambda rules: [[*_half_forward(rules), *_half_forward(rules)]],
    MotionKind.HCB_X2: lambda rules: [[*_half_back(rules), *_half_back(rules)]],
    MotionKind.QCF_DP: lambda rules: [[*_quarter_forward(rules), (_ONLY_DOWN, False), (_ONLY_DF, False)]],
    MotionKind.QCB_RDP: lambda rules: [[*_quarter_back(rules), (_ONLY_DOWN, False), (_ONLY_DB, False)]],
    MotionKind.QCF_UF: lambda rules: [[*_quarter_forward(rules), (_ONLY_UF, False)]],
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
    """

    max_skip: int
    tail_skip: int = 0
    max_gap_ms: int = _UNBOUNDED


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
        allowed, _ = steps[pi]
        skip = limits.tail_skip if pi == last else limits.max_skip
        found = []
        for j in range(si, max(-1, si - skip - 1), -1):
            if successor >= 0 and states[successor].start_ms - states[j].start_ms > limits.max_gap_ms:
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
    return _Limits(
        max_skip=ruleset.max_intermediate,
        tail_skip=ruleset.tail_states,
        max_gap_ms=_UNBOUNDED if context.loose else ruleset.step_gap_ms + context.decay_ms,
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
    MotionKind.CHARGE_BF: (BACK_DIRECTIONS, [(FORWARD_DIRECTIONS, False)]),
    MotionKind.CHARGE_DU: (DOWN_DIRECTIONS, [(UP_DIRECTIONS, False)]),
    MotionKind.CHARGE_BFBF: (
        BACK_DIRECTIONS,
        [(FORWARD_DIRECTIONS, False), (BACK_DIRECTIONS, False), (FORWARD_DIRECTIONS, False)],
    ),
    MotionKind.CHARGE_DB_UF: (
        frozenset({_D.DOWN_BACK, _D.DOWN}),
        [(_ONLY_DF, False), (_ONLY_DB, False), (frozenset({_D.UP_FORWARD, _D.UP}), False)],
    ),
}


def _match_charge(kind: MotionKind, buffer: InputBuffer, context: MatchContext) -> bool:
    ruleset, at_ms, decay_ms = context.ruleset, context.at_ms, context.decay_ms
    charge_dirs, release_steps = _CHARGE_DEFINITIONS[kind]
    states = list(buffer.directions)
    release_budget = ruleset.charge_release_ms + (ruleset.motion_window_ms + decay_ms) * len(release_steps)
    for index in range(len(states) - 1, -1, -1):
        state = states[index]
        if state.direction not in charge_dirs:
            continue
        if state.duration_ms(at_ms) < ruleset.charge_ms:
            continue
        if state.end_ms is None or at_ms - state.end_ms > release_budget:
            continue
        if _find_steps(states[index + 1 :], release_steps, _limits(context)) is not None:
            return True
    return False


def _ring_index(direction: Direction) -> int | None:
    try:
        return DIRECTION_RING.index(direction)
    except ValueError:
        return None


def _match_rotation(turns: int, buffer: InputBuffer, ruleset: Ruleset, at_ms: int) -> bool:
    """Detect ``turns`` full circles.

    Rather than demanding all eight directions, this accumulates how far around
    the ring the stick has travelled without reversing, which is what lets a
    hitbox player get a 360 out of four cardinal presses.
    """
    horizon = at_ms - ruleset.rotation_window_ms * turns
    indices = [i for i in (_ring_index(s.direction) for s in buffer.directions_since(horizon)) if i is not None]
    needed = max(4, 8 * turns - ruleset.rotation_slack * turns)
    for direction in (1, -1):
        travelled = 0
        previous: int | None = None
        for index in indices:
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


def _match_mash(spec: MotionSpec, buffer: InputBuffer, ruleset: Ruleset, at_ms: int) -> bool:
    recent = buffer.buttons_since(at_ms - ruleset.mash_window_ms)
    hits = sum(1 for press in recent if press.button in spec.buttons.allowed)
    return hits >= ruleset.mash_count


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
    """Whether ``spec`` is satisfied by the buffer at the moment of this press."""
    ruleset, at_ms = context.ruleset, context.at_ms
    if len(context.pressed & spec.buttons.allowed) < spec.buttons.count:
        return False
    if spec.air and not _match_air(buffer, at_ms):
        return False

    simple = _SIMPLE_MATCHERS.get(spec.kind)
    if simple is not None:
        return simple(spec, buffer, ruleset, at_ms)
    if spec.kind in CHARGE_KINDS:
        return _match_charge(spec.kind, buffer, context)
    return _match_directional(spec.kind, buffer, context)
