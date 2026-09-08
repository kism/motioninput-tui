"""Timestamped input history that motion matchers read from.

Everything in here is measured in milliseconds since an arbitrary origin, so
the engine never touches the clock itself and stays trivially testable.
"""

from collections import deque
from dataclasses import dataclass, field

from .notation import Button, Direction

DEFAULT_RETENTION_MS = 4000
"""How much history to keep. Comfortably longer than the slowest charge move."""


@dataclass(slots=True)
class DirectionState:
    """A direction that was held from ``start_ms`` until ``end_ms``."""

    direction: Direction
    start_ms: int
    end_ms: int | None = None

    def duration_ms(self, now_ms: int) -> int:
        """How long this direction has been (or was) held."""
        return (self.end_ms if self.end_ms is not None else now_ms) - self.start_ms

    @property
    def is_current(self) -> bool:
        """Whether this is the direction being held right now."""
        return self.end_ms is None


@dataclass(slots=True)
class ButtonPress:
    """A single attack button going down."""

    button: Button
    at_ms: int


@dataclass(slots=True)
class InputBuffer:
    """Rolling history of directions and button presses.

    Buttons pressed within ``simultaneous_ms`` of each other are treated as one
    press, which is what makes ``PP``/``KKK`` inputs possible on a keyboard.
    """

    retention_ms: int = DEFAULT_RETENTION_MS
    simultaneous_ms: int = 40
    directions: deque[DirectionState] = field(default_factory=deque)
    buttons: deque[ButtonPress] = field(default_factory=deque)

    def set_direction(self, direction: Direction, at_ms: int) -> bool:
        """Record the currently held direction. Returns True if it changed."""
        if self.directions and self.directions[-1].direction == direction and self.directions[-1].is_current:
            return False
        if self.directions and self.directions[-1].is_current:
            self.directions[-1].end_ms = at_ms
        self.directions.append(DirectionState(direction, at_ms))
        self._trim(at_ms)
        return True

    def press_button(self, button: Button, at_ms: int) -> None:
        """Record an attack button press."""
        self.buttons.append(ButtonPress(button, at_ms))
        self._trim(at_ms)

    def current_direction(self, default: Direction = Direction.NEUTRAL) -> Direction:
        """The direction held right now."""
        if self.directions and self.directions[-1].is_current:
            return self.directions[-1].direction
        return default

    def directions_since(self, since_ms: int) -> list[DirectionState]:
        """Direction states that were active at any point after ``since_ms``."""
        return [state for state in self.directions if state.end_ms is None or state.end_ms >= since_ms]

    def buttons_since(self, since_ms: int) -> list[ButtonPress]:
        """Button presses made after ``since_ms``."""
        return [press for press in self.buttons if press.at_ms >= since_ms]

    def simultaneous_buttons(self, at_ms: int) -> set[Button]:
        """Buttons pressed close enough to ``at_ms`` to count as one input."""
        return {press.button for press in self.buttons if abs(press.at_ms - at_ms) <= self.simultaneous_ms}

    def consume(self, at_ms: int) -> None:
        """Flush the command buffer because a move just came out.

        Games scan a rolling buffer of recent inputs and clear it once a
        special move activates, so the inputs that produced it cannot go on to
        feed another one. Without this, two quarter circles in a row read as
        the double quarter circle of a super.

        The direction being held survives, since the player has not physically
        let go of it, but it starts counting from now: a charge is spent.
        """
        current = self.current_direction()
        self.directions.clear()
        self.buttons.clear()
        self.directions.append(DirectionState(current, at_ms))

    def clear(self) -> None:
        """Drop all history."""
        self.directions.clear()
        self.buttons.clear()

    def _trim(self, now_ms: int) -> None:
        cutoff = now_ms - self.retention_ms
        while self.buttons and self.buttons[0].at_ms < cutoff:
            self.buttons.popleft()
        while len(self.directions) > 1 and self.directions[0].end_ms is not None and self.directions[0].end_ms < cutoff:
            self.directions.popleft()
