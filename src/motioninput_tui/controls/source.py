"""Input sources: things that turn a device into directions and buttons."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from motioninput_tui.engine.notation import Button, Direction, direction_from_axes

from .layouts import DEFAULT_TIMING, Axis, HeldAxes, HoldTiming

if TYPE_CHECKING:
    from .layouts import ControlLayout


@dataclass(frozen=True, slots=True)
class SourceUpdate:
    """What a device did at a moment in time."""

    direction: Direction
    button: Button | None = None
    direction_changed: bool = False


@dataclass
class KeyboardSource:
    """Reads a :class:`ControlLayout` and infers which directions are held.

    The only input source there is: the gamepad reuses this in exact mode
    (:mod:`motioninput_tui.controls.gamepad` polls the pad and feeds its
    presses and releases straight through), since a pad reports real releases
    and never needs holds inferred.

    See :class:`~.layouts.HoldTiming` for how holds are deduced from presses
    and auto-repeats, which is the one place this trainer has to approximate
    what a real controller would tell a real game.
    """

    layout: ControlLayout
    timing: HoldTiming = DEFAULT_TIMING
    exact: bool = False
    """Set when the terminal is known to report key releases, so holds never
    have to be inferred, not even for the very first input."""
    _axes: HeldAxes = field(init=False)
    _direction: Direction = field(default=Direction.NEUTRAL, init=False)

    def __post_init__(self) -> None:
        """Set up hold tracking with the configured timings."""
        self._axes = HeldAxes(timing=self.timing, exact=self.exact)

    @property
    def direction(self) -> Direction:
        """The direction currently being held."""
        return self._direction

    def press(self, code: str, at_ms: int) -> SourceUpdate | None:
        """Handle a key press, returning what it means or None if unbound."""
        binding = self.layout.bindings.get(code)
        if binding is None:
            return None
        if not isinstance(binding, Axis):
            return self._update(button=binding)

        self._axes.press(binding, at_ms)
        return self._update(button=None)

    def release(self, code: str, at_ms: int) -> SourceUpdate | None:
        """Handle a key release reported by the terminal.

        Only movement keys matter: attack buttons are momentary, and the engine
        already treats them as an instant at which a move is attempted.
        """
        binding = self.layout.bindings.get(code)
        if not isinstance(binding, Axis):
            # Still tell the axis tracker, so it knows releases are available.
            self._axes.note_release_support()
            return None
        self._axes.release(binding, at_ms)
        return self._update(button=None)

    @property
    def repeat_delay_ms(self) -> int:
        """The keyboard's measured initial repeat delay, 0 if not yet seen."""
        return self._axes.observed_repeat_delay_ms

    @property
    def tap_ms(self) -> int:
        """The window a single press is treated as held for."""
        return self._axes.tap_ms

    @property
    def decay_ms(self) -> int:
        """How long this device takes to reveal that a direction was released.

        Zero once the terminal reports releases, which lets the engine judge
        motions against the games' real timing windows.
        """
        return 0 if self._axes.exact else self._axes.tap_ms

    @property
    def exact_holds(self) -> bool:
        """Whether holds are known from real releases rather than inferred."""
        return self._axes.exact

    def tick(self, at_ms: int) -> SourceUpdate | None:
        """Expire stale holds. Returns an update only when something changed."""
        if not self._axes.expire(at_ms):
            return None
        return self._update(button=None)

    def reset(self) -> None:
        """Release every held direction."""
        self._axes.clear()
        self._direction = Direction.NEUTRAL

    def _update(self, button: Button | None) -> SourceUpdate:
        held = self._axes.held()
        direction = direction_from_axes(
            left=Axis.LEFT in held,
            right=Axis.RIGHT in held,
            down=Axis.DOWN in held,
            up=Axis.UP in held,
            last_horizontal=self._axes.newer_horizontal(),
        )
        changed = direction != self._direction
        self._direction = direction
        return SourceUpdate(direction=direction, button=button, direction_changed=changed)
