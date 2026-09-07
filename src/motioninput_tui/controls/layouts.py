"""Physical control layouts.

Only keyboards are implemented, but everything downstream talks to
:class:`ControlLayout`, so adding a gamepad means adding a layout and a source
rather than touching the engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from motioninput_tui.engine.notation import Button


class Axis(StrEnum):
    """One of the four movement inputs."""

    LEFT = "left"
    RIGHT = "right"
    DOWN = "down"
    UP = "up"


class LayoutKind(StrEnum):
    """The device family a layout is for."""

    KEYBOARD = "keyboard"
    GAMEPAD = "gamepad"


@dataclass(frozen=True, slots=True)
class ControlLayout:
    """A mapping from physical inputs to directions and attack buttons."""

    key: str
    name: str
    description: str
    movement: dict[str, Axis]
    attacks: dict[str, Button]
    kind: LayoutKind = LayoutKind.KEYBOARD
    available: bool = True

    @property
    def bindings(self) -> dict[str, Axis | Button]:
        """Every binding in one dict, for lookup on a key press."""
        combined: dict[str, Axis | Button] = dict(self.movement)
        combined.update(self.attacks)
        return combined

    def movement_help(self) -> str:
        """Human readable movement bindings, e.g. 'a s d space'."""
        order = (Axis.LEFT, Axis.DOWN, Axis.RIGHT, Axis.UP)
        by_axis = {axis: key for key, axis in self.movement.items()}
        return " ".join(_display_key(by_axis[axis]) for axis in order if axis in by_axis)

    def attack_help(self) -> str:
        """Human readable attack bindings, e.g. 'LP=u MP=i ...'."""
        by_button = {button: key for key, button in self.attacks.items()}
        return " ".join(f"{button.value}={_display_key(by_button[button])}" for button in Button if button in by_button)


def _display_key(key: str) -> str:
    return "␣" if key == "space" else key


HITBOX = ControlLayout(
    key="hitbox",
    name="Hitbox",
    description="Left hand on a s d for back/down/forward, space for up. Attacks on u i o / j k l.",
    movement={"a": Axis.LEFT, "s": Axis.DOWN, "d": Axis.RIGHT, "space": Axis.UP},
    attacks={
        "u": Button.LP,
        "i": Button.MP,
        "o": Button.HP,
        "j": Button.LK,
        "k": Button.MK,
        "l": Button.HK,
    },
)

SOUTHPAW = ControlLayout(
    key="southpaw",
    name="Southpaw",
    description="Right hand on j k l for back/down/forward, space for up. Attacks on q w e / a s d.",
    movement={"j": Axis.LEFT, "k": Axis.DOWN, "l": Axis.RIGHT, "space": Axis.UP},
    attacks={
        "q": Button.LP,
        "w": Button.MP,
        "e": Button.HP,
        "a": Button.LK,
        "s": Button.MK,
        "d": Button.HK,
    },
)

GAMEPAD = ControlLayout(
    key="gamepad",
    name="Gamepad",
    description="Not implemented yet. The engine is device agnostic, so this only needs an input source.",
    movement={},
    attacks={},
    kind=LayoutKind.GAMEPAD,
    available=False,
)

LAYOUTS: dict[str, ControlLayout] = {layout.key: layout for layout in (HITBOX, SOUTHPAW, GAMEPAD)}
DEFAULT_LAYOUT = HITBOX.key


def get_layout(key: str) -> ControlLayout:
    """Look up a layout by key, raising a helpful error for unknown names."""
    try:
        return LAYOUTS[key]
    except KeyError:
        known = ", ".join(LAYOUTS)
        message = f"Unknown layout {key!r}. Known layouts: {known}"
        raise KeyError(message) from None


def available_layouts() -> list[ControlLayout]:
    """Layouts that can actually be used right now."""
    return [layout for layout in LAYOUTS.values() if layout.available]


@dataclass(frozen=True, slots=True)
class HoldTiming:
    """Timings for inferring key holds from presses alone.

    Terminals report key presses and operating system auto-repeats but never
    releases, so a held key has to be deduced:

    * A press marks its axis held for ``tap_ms``. That is long enough for a
      hitbox player to add a second direction and get a diagonal, and short
      enough that the first direction drops away again on its own, which is
      what produces the d, df, f transitions of a quarter circle.
    * Auto-repeat arrives as a burst of presses only milliseconds apart. Once
      ``repeats_to_confirm`` of those have been seen the key is genuinely
      being held, so the window widens to ``hold_ms`` and the hold is
      back-dated to the original press. That is what makes charge moves
      possible.
    * ``bridge_ms`` covers the operating system's initial repeat delay, the
      quiet gap between the first press and the start of the repeat burst.
    * A deliberate double tap of one key has gaps far wider than
      ``repeat_gap_ms``, so it is never mistaken for auto-repeat. This matters:
      it is exactly the input that separates a 3rd Strike dragon punch from a
      fireball.
    """

    tap_ms: int = 250
    hold_ms: int = 300
    repeat_gap_ms: int = 80
    repeats_to_confirm: int = 2
    bridge_ms: int = 1200
    adapt: bool = True
    max_tap_ms: int = 700


DEFAULT_TIMING = HoldTiming()

TAP_MARGIN_MS = 60
"""Headroom added to the measured repeat delay when adapting ``tap_ms``."""

MIN_REPEAT_DELAY_MS = 120
"""No keyboard repeats faster than this, so shorter gaps are not repeat delays."""

COMFORTABLE_REPEAT_DELAY_MS = 300
"""Above this, holds are noticeably late to register and motions feel sluggish."""


def repeat_delay_advice(observed_ms: int) -> str:
    """Advice for a keyboard whose repeat delay is slowing the trainer down.

    Held directions can only be detected through auto-repeat, so a long initial
    repeat delay directly widens every motion window. Empty when nothing is
    wrong, or when no repeat has been observed yet.
    """
    if observed_ms <= COMFORTABLE_REPEAT_DELAY_MS:
        return ""
    return (
        f"Key repeat delay is about {observed_ms}ms, which makes held directions slow to register. "
        "Lower it for tighter timing: macOS `defaults write -g InitialKeyRepeat -int 15` (log out and back in), "
        "X11 `xset r rate 200 40`, or your compositor's repeat-delay setting on Wayland."
    )


@dataclass(slots=True)
class AxisHold:
    """One movement axis being held down."""

    first_ms: int
    last_ms: int
    fast_repeats: int = 0
    confirmed: bool = False
    pending_delay_ms: int = 0
    """Gap back to a hold that just lapsed. Only believed as the keyboard's
    repeat delay once this hold turns out to be a genuine auto-repeat burst."""


@dataclass(slots=True)
class PressResult:
    """What a movement key press meant."""

    started: bool = False
    """True when this began a new hold rather than refreshing one."""


@dataclass(slots=True)
class HeldAxes:
    """Tracks which movement axes are down, inferring holds from auto-repeat.

    ``tap_ms`` should sit just above the operating system's initial key-repeat
    delay, so that a genuinely held key keeps repeating before its window
    lapses. That delay is a user setting, so it is measured as the player types
    and the window is widened to match. Until then, holding a direction can
    briefly read as a tap.
    """

    timing: HoldTiming = DEFAULT_TIMING
    holds: dict[Axis, AxisHold] = field(default_factory=dict)
    tap_ms: int = 0
    observed_repeat_delay_ms: int = 0
    _expired: dict[Axis, AxisHold] = field(default_factory=dict)
    _samples: list[int] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Start from the configured tap window."""
        self.tap_ms = self.tap_ms or self.timing.tap_ms

    def press(self, axis: Axis, at_ms: int) -> PressResult:
        """Register a press or auto-repeat of a movement key."""
        hold = self.holds.get(axis)
        if hold is not None and at_ms - hold.last_ms <= self._window(hold):
            return self._refresh(hold, at_ms)

        pending = 0
        ghost = self._expired.pop(axis, None)
        if ghost is not None and at_ms - ghost.last_ms <= self.timing.bridge_ms:
            pending = at_ms - ghost.first_ms
        self.holds[axis] = AxisHold(first_ms=at_ms, last_ms=at_ms, pending_delay_ms=pending)
        return PressResult(started=True)

    def _observe_repeat_delay(self, delay_ms: int) -> None:
        """Learn the keyboard's initial repeat delay and widen ``tap_ms``.

        Called only once a hold has been proved genuine by a burst of fast
        auto-repeats, so the gap that preceded the burst really was the
        operating system's initial repeat delay rather than the player tapping
        the same key twice.
        """
        if not delay_ms >= MIN_REPEAT_DELAY_MS or delay_ms <= self.tap_ms:
            return
        self._samples.append(delay_ms)
        del self._samples[:-4]
        self.observed_repeat_delay_ms = max(self.observed_repeat_delay_ms, delay_ms)
        if self.timing.adapt:
            self.tap_ms = min(delay_ms + TAP_MARGIN_MS, self.timing.max_tap_ms)

    def _refresh(self, hold: AxisHold, at_ms: int) -> PressResult:
        gap = at_ms - hold.last_ms
        hold.last_ms = at_ms
        if gap > self.timing.repeat_gap_ms:
            hold.fast_repeats = 0
            return PressResult()
        hold.fast_repeats += 1
        if hold.fast_repeats >= self.timing.repeats_to_confirm and not hold.confirmed:
            # A burst of presses milliseconds apart is auto-repeat, not typing,
            # so widen the window and stop treating this as a tap.
            hold.confirmed = True
            if hold.pending_delay_ms:
                self._observe_repeat_delay(hold.pending_delay_ms)
        return PressResult()

    def expire(self, at_ms: int) -> bool:
        """Drop axes that have stopped repeating. Returns True if any changed."""
        stale = [axis for axis, hold in self.holds.items() if at_ms - hold.last_ms > self._window(hold)]
        for axis in stale:
            self._expired[axis] = self.holds.pop(axis)
        for axis, ghost in list(self._expired.items()):
            if at_ms - ghost.last_ms > self.timing.bridge_ms:
                del self._expired[axis]
        return bool(stale)

    def held(self) -> frozenset[Axis]:
        """The axes currently considered held."""
        return frozenset(self.holds)

    def newer_horizontal(self) -> str:
        """Which of left/right was pressed most recently, for SOCD cleaning."""
        left, right = self.holds.get(Axis.LEFT), self.holds.get(Axis.RIGHT)
        if left is None or right is None:
            return ""
        return "left" if left.first_ms > right.first_ms else "right"

    def held_since(self, axes: frozenset[Axis]) -> int | None:
        """When the combination of ``axes`` became complete."""
        starts = [self.holds[axis].first_ms for axis in axes if axis in self.holds]
        return max(starts) if starts else None

    def clear(self) -> None:
        """Release everything."""
        self.holds.clear()
        self._expired.clear()

    def _window(self, hold: AxisHold) -> int:
        return self.timing.hold_ms if hold.confirmed else self.tap_ms
