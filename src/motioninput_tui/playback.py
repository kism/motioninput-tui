"""A move played back: the keys that bring it out, at the timing its game gives most room.

Nothing here models a game's timing, since the engine already does. A timing is
found by asking it: the move is performed through a session of its own at a
range of paces, and the one played sits halfway between a single frame a step
and the slowest the game still takes. A player copying it has as much room to be
early as to be late.

A charge is held a little past what the game asks, a mash goes at a comfortable
twelve presses a second, and deliberate taps sit in the middle of the gap the
recogniser allows between them. The search then proves the whole script lands.
"""

from dataclasses import dataclass, replace
from itertools import combinations, groupby
from operator import attrgetter
from typing import TYPE_CHECKING

from motioninput_tui.controls.layouts import Axis, LayoutKind
from motioninput_tui.engine.motions import CHARGE_KINDS, MotionKind
from motioninput_tui.engine.notation import Button, Direction
from motioninput_tui.engine.recognizer import (
    RHYTHM_TAP_MAX_GAP_MS,
    RHYTHM_TAP_MIN_GAP_MS,
    SUPER_CATEGORY,
    FollowUpStatus,
)
from motioninput_tui.engine.session import TrainingSession
from motioninput_tui.notation_styles import CHARGES, motion_path

if TYPE_CHECKING:
    from motioninput_tui.controls.layouts import ControlLayout
    from motioninput_tui.engine.motions import MotionSpec
    from motioninput_tui.engine.ruleset import Ruleset
    from motioninput_tui.games.models import Character, Game, Move

FRAME_MS = 1000 / 60

FASTEST_STEP_MS = 17
"""A frame a step, as quick as a hand gets. The fast end of the range searched."""
SLOWEST_STEP_MS = 300
"""The slow end: a move that still lands with steps this far apart is not timed by them."""
FALLBACK_STEP_MS = 83
"""What a move no pace brings out is shown at, so the player sees what it gives instead."""

MASH_GAP_MS = 83
"""Five frames between presses of a mash, twelve a second."""
BUTTON_HOLD_MS = 83
"""How long a button stays down, which only the panel sees."""
CHARGE_SPARE_MS = 100
"""Held past the game's charge time, since a charge let go a frame early is nothing."""

TICK_MS = 8
"""How finely a playback's clock runs between presses, as the motion tests' does."""
SETTLE_MS = 250
"""Clock left running after the last press, for a late activation or a follow-through's verdict."""

_D = Direction
_AXES: dict[Direction, frozenset[Axis]] = {
    _D.DOWN_BACK: frozenset({Axis.DOWN, Axis.LEFT}),
    _D.DOWN: frozenset({Axis.DOWN}),
    _D.DOWN_FORWARD: frozenset({Axis.DOWN, Axis.RIGHT}),
    _D.BACK: frozenset({Axis.LEFT}),
    _D.NEUTRAL: frozenset(),
    _D.FORWARD: frozenset({Axis.RIGHT}),
    _D.UP_BACK: frozenset({Axis.UP, Axis.LEFT}),
    _D.UP: frozenset({Axis.UP}),
    _D.UP_FORWARD: frozenset({Axis.UP, Axis.RIGHT}),
}
_DIRECTIONS = {axes: direction for direction, axes in _AXES.items()}

# Forward round through down to up: a 270, which passes over all four cardinals
# and ends on the up, a jump, so the button follows it at once. A 720 is two of
# them, the stick snapping from up straight back to forward between, as it is
# done on a leverless: the cardinals are what counts, not a second full turn.
_CIRCLE = (_D.FORWARD, _D.DOWN_FORWARD, _D.DOWN, _D.DOWN_BACK, _D.BACK, _D.UP_BACK, _D.UP)
_ROTATIONS = {MotionKind.ROTATE_360: _CIRCLE, MotionKind.ROTATE_720: (*_CIRCLE, *_CIRCLE)}


@dataclass(frozen=True, slots=True)
class Event:
    """A key going down or coming up, some milliseconds into the playback."""

    at_ms: int
    key: str
    down: bool


@dataclass(frozen=True, slots=True)
class Timing:
    """The script a move is played back with, and what the search made of it."""

    events: tuple[Event, ...]
    step_ms: int
    """The gap between one direction and the next."""
    slowest_ms: int | None = None
    """The slowest step the game still takes. None when the steps are not what times the move."""
    works: bool = True
    instead: tuple[str, ...] = ()
    """What came out when nothing brought the move out, which is what the playback shows."""


class _Script:
    """Keys on a timeline, laid down one direction or button at a time."""

    def __init__(self, layout: ControlLayout) -> None:
        self.keys = {axis: key for key, axis in layout.movement.items()}
        self.events: list[Event] = []
        self.held: frozenset[Axis] = frozenset()
        self.at = 0

    def stick(self, direction: Direction) -> None:
        """Move to ``direction``, letting go first so opposite keys are never held together."""
        axes = _AXES[direction]
        self.events += [Event(self.at, self.keys[axis], down=False) for axis in sorted(self.held - axes)]
        self.events += [Event(self.at, self.keys[axis], down=True) for axis in sorted(axes - self.held)]
        self.held = axes

    def press(self, keys: tuple[str, ...], hold_ms: int) -> None:
        """Press ``keys`` together now and let them go ``hold_ms`` later."""
        self.events += [Event(self.at, key, down=True) for key in keys]
        self.events += [Event(self.at + hold_ms, key, down=False) for key in keys]

    def done(self) -> tuple[Event, ...]:
        # Stable, so what happens in one millisecond keeps the order it was laid down in.
        return tuple(sorted(self.events, key=attrgetter("at_ms")))


def _path(spec: MotionSpec) -> tuple[Direction, ...]:
    """The directions a move is performed through, after any charge."""
    if spec.kind is MotionKind.HOLD:
        return () if spec.hold is None else (spec.hold,)
    if spec.kind in CHARGE_KINDS:
        return CHARGES[spec.kind][1]
    return _ROTATIONS.get(spec.kind) or motion_path(spec.kind)


def _script(move: Move, ruleset: Ruleset, layout: ControlLayout, keys: tuple[str, ...], step_ms: int) -> Timing:
    """``move`` performed with ``keys`` for its buttons, ``step_ms`` between directions."""
    spec = move.motion
    assert spec is not None  # ruff: ignore[assert] - only trainable moves are played back
    script = _Script(layout)
    if spec.air:  # jump, and do the motion once off the ground, or the move on the ground wins
        script.stick(_D.UP)
        script.at += max(step_ms, ruleset.jump_grace_ms + FASTEST_STEP_MS)
    if spec.kind in CHARGE_KINDS:
        script.stick(CHARGES[spec.kind][0])
        script.at += ruleset.charge_ms + CHARGE_SPARE_MS
    path = _path(spec)
    for index, direction in enumerate(path):
        script.at += step_ms if index else 0
        script.stick(direction)
    script.at += step_ms // 2 if path else 0
    if spec.kind is MotionKind.MASH:
        gap = min(MASH_GAP_MS, ruleset.mash_window_ms // ruleset.mash_count)
        for _ in range(ruleset.mash_count):
            script.press(keys[:1], gap // 2)
            script.at += gap
    elif spec.mash:
        rhythm = (RHYTHM_TAP_MIN_GAP_MS + RHYTHM_TAP_MAX_GAP_MS) // 2
        gap = rhythm if spec.mash_rhythm else MASH_GAP_MS
        script.press(keys, gap // 2)
        # A super's taps wait out its cinematic, where the game reads nothing.
        script.at += ruleset.super_freeze_ms if move.category == SUPER_CATEGORY else 0
        tap = _tap_key(spec, layout, keys)
        for _ in range(spec.mash):
            script.at += gap
            script.press((tap,), gap // 2)
        script.at += gap // 2
    else:
        script.press(keys, BUTTON_HOLD_MS)
        script.at += BUTTON_HOLD_MS
    script.stick(_D.NEUTRAL)
    return Timing(script.done(), step_ms)


def _panel(layout: ControlLayout) -> dict[Button, str]:
    """Each button the layout has, and the first key it is on, in panel order."""
    keys: dict[Button, str] = {}
    for row in layout.bound_rows():
        for key, button in row:
            keys.setdefault(button, key)
    return keys


def _tap_key(spec: MotionSpec, layout: ControlLayout, keys: tuple[str, ...]) -> str:
    """The key a follow-through is tapped on: the move's own, unless it wants the other kind of button."""
    if not spec.mash_button:
        return keys[0]
    return next(key for button, key in _panel(layout).items() if button in spec.follow_up_buttons)


class Run:
    """A timing being played through a session of its own, on a clock of its own.

    The clock runs on a fixed grid of ticks with every press landing at its own
    moment, however :meth:`advance` is called, so the playback on screen goes
    exactly as the search that proved it did.
    """

    def __init__(self, game: Game, character: Character, layout: ControlLayout, move: Move, timing: Timing) -> None:
        """Set a fresh session up for ``move``, with its Super Art equipped."""
        # A keyboard, whatever the player is on, or a gamepad layout opens a
        # second reader onto the real pad. Nothing played back holds opposite
        # directions, so the keyboard's SOCD never comes into it.
        keyboard = replace(layout, kind=LayoutKind.KEYBOARD)
        self.session = TrainingSession(game, character, keyboard, exact_input=True)
        if move.super_art:
            self.session.select_super_art(move.super_art)
        self.move = move
        self.timing = timing
        self.now = 0
        self._next = 0

    @property
    def finished(self) -> bool:
        """Whether every key has been pressed and let go."""
        return self._next >= len(self.timing.events)

    @property
    def landed(self) -> bool:
        """Whether the move came out, follow-through and all."""
        return any(
            activation.move is self.move
            and (activation.follow_up is None or activation.follow_up.status is FollowUpStatus.COMPLETE)
            for activation in self.session.activations
        )

    def advance(self, to_ms: int) -> bool:
        """Play on to ``to_ms`` into the playback. True if the session changed."""
        events = self.timing.events
        changed = False
        while True:
            grid = self.now - self.now % TICK_MS + TICK_MS
            now = min(grid, events[self._next].at_ms) if not self.finished else grid
            if now > to_ms:
                return changed
            self.now = now
            while not self.finished and events[self._next].at_ms <= now:
                event = events[self._next]
                self._next += 1
                feed = self.session.press if event.down else self.session.release
                changed |= feed(event.key, event.at_ms)
            changed |= self.session.tick(now)


def plan(game: Game, character: Character, layout: ControlLayout, move: Move) -> Timing:
    """How to play ``move`` back: the pace that gives most room, proven to bring it out.

    Each way of pressing its buttons is tried in panel order, the lightest
    first, until one lands at a frame a step. The slowest step that still lands
    is found by halving, on the reasonable view that a motion slow enough to
    fail is not rescued by going slower still, and the step played is halfway
    between the two.
    """
    spec = move.motion
    assert spec is not None  # ruff: ignore[assert] - only trainable moves are played back
    panel = _panel(layout)
    usable = [button for button in panel if button in spec.buttons.allowed]
    choices = list(combinations(usable, spec.buttons.count)) or [tuple(usable)]

    def lands(timing: Timing) -> bool:
        run = Run(game, character, layout, move, timing)
        run.advance(timing.events[-1].at_ms + SETTLE_MS)
        return run.landed

    for buttons in choices:
        keys = tuple(panel[button] for button in buttons)

        def at(step_ms: int, keys: tuple[str, ...] = keys) -> Timing:
            return _script(move, game.ruleset, layout, keys, step_ms)

        if not lands(at(FASTEST_STEP_MS)):
            continue
        if lands(at(SLOWEST_STEP_MS)):
            return replace(at((FASTEST_STEP_MS + SLOWEST_STEP_MS) // 2), slowest_ms=None)
        quick, slow = FASTEST_STEP_MS, SLOWEST_STEP_MS
        while slow - quick > 1:
            middle = (quick + slow) // 2
            quick, slow = (middle, slow) if lands(at(middle)) else (quick, middle)
        chosen = at((FASTEST_STEP_MS + quick) // 2)
        return replace(chosen if lands(chosen) else at(quick), slowest_ms=quick)

    keys = tuple(panel[button] for button in choices[0])
    timing = _script(move, game.ruleset, layout, keys, FALLBACK_STEP_MS)
    run = Run(game, character, layout, move, timing)
    run.advance(timing.events[-1].at_ms + SETTLE_MS)
    instead = tuple(activation.name for activation in reversed(run.session.activations))
    return replace(timing, works=False, instead=instead)


type Beat = tuple[int, Direction | tuple[Button, ...]]
"""A moment in a playback and what happens at it: the stick arriving somewhere, or buttons going down."""


def beats(timing: Timing, layout: ControlLayout) -> list[Beat]:
    """What a playback does, in order, for writing out with the gaps between.

    The stick coming back to neutral at the end is left off, since it is
    letting go rather than part of the move.
    """
    held: set[Axis] = set()
    direction = _D.NEUTRAL
    found: list[Beat] = []
    for at_ms, group in groupby(timing.events, key=attrgetter("at_ms")):
        pressed: list[Button] = []
        for event in group:
            axis = layout.movement.get(event.key)
            if axis is None:
                if event.down:
                    pressed.append(layout.attacks[event.key])
            elif event.down:
                held.add(axis)
            else:
                held.discard(axis)
        now = _DIRECTIONS[frozenset(held)]
        if now is not direction and now is not _D.NEUTRAL:
            found.append((at_ms, now))
        direction = now
        if pressed:
            found.append((at_ms, tuple(pressed)))
    return found
