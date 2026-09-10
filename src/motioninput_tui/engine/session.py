"""A training session: one game, one character, one control layout."""

import time
from collections import deque
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from motioninput_tui.controls.layouts import LayoutKind, repeat_delay_advice
from motioninput_tui.controls.source import KeyboardSource
from motioninput_tui.utils.logger import get_logger

from .buffer import InputBuffer
from .notation import Button, Direction
from .recognizer import Activation, BufferPolicy, Recognizer

if TYPE_CHECKING:
    from motioninput_tui.controls.gamepad import GamepadReader
    from motioninput_tui.controls.layouts import ControlLayout
    from motioninput_tui.games.models import Character, Game, Move

logger = get_logger(__name__)

HISTORY_LENGTH = 40
"""How many input entries the strip remembers."""

ACTIVATION_LENGTH = 12
"""How many activated moves to keep in the feed."""


def monotonic_ms() -> int:
    """Milliseconds from a monotonic clock."""
    return time.monotonic_ns() // 1_000_000


@dataclass(slots=True)
class InputEntry:
    """One column of the input display."""

    direction: Direction
    at_ms: int
    buttons: list[Button] = field(default_factory=list)
    activated: str | None = None


class TrainingSession:
    """Wires an input source, an input buffer and a move recogniser together.

    The caller drives it with :meth:`press` and :meth:`tick`; everything else
    is read-only state for the interface to render.
    """

    def __init__(
        self,
        game: Game,
        character: Character,
        layout: ControlLayout,
        *,
        exact_input: bool = False,
        policy: BufferPolicy = BufferPolicy.CONSUME,
    ) -> None:
        """Set up the buffer, source and recogniser for this pairing.

        ``exact_input`` says the terminal reports key releases, so holds are
        tracked exactly from the first keystroke rather than after the first
        release has proved it. ``policy`` decides whether the inputs that
        produced a move are spent. The game's rules are taken as they come:
        the player's settings are folded into them beforehand by
        :func:`motioninput_tui.settings.tuned_game`.
        """
        self.game = game
        self.character = character
        self.layout = layout
        self.ruleset = game.ruleset
        self.buffer = InputBuffer()
        self.gamepad = self._open_gamepad(layout)
        # A gamepad reports releases, so holds are always exact with one attached.
        self.source = KeyboardSource(layout, exact=exact_input or self.gamepad is not None)
        # 3rd Strike equips one Super Art of three; everywhere else this is empty
        # and every move stays live.
        self.super_arts: tuple[str, ...] = character.super_arts
        self.super_art = self.super_arts[0] if self.super_arts else ""
        self.recognizer = Recognizer(self._live_moves(), self.ruleset, policy=policy)
        self.entries: deque[InputEntry] = deque(maxlen=HISTORY_LENGTH)
        self.activations: deque[Activation] = deque(maxlen=ACTIVATION_LENGTH)
        self.total_inputs = 0
        self.total_activations = 0
        logger.debug(
            "Session: %s / %s / %s, %d trainable moves",
            game.short_name,
            character.name,
            layout.name,
            len(character.trainable_moves),
        )

    @staticmethod
    def _open_gamepad(layout: ControlLayout) -> GamepadReader | None:
        """A gamepad reader when the layout wants one, else None.

        pygame is a heavy optional import, so it only happens here, and only
        for the gamepad layout.
        """
        if layout.kind is not LayoutKind.GAMEPAD:
            return None
        from motioninput_tui.controls.gamepad import (  # ruff: ignore[import-outside-top-level] - optional dependency, gamepad layout only
            GamepadReader,
        )

        reader = GamepadReader()
        if not reader.available:
            logger.warning("Gamepad layout selected but pygame is not installed")
        return reader

    def _live_moves(self) -> list[Move]:
        """The character's moves, minus the Super Arts that are not equipped."""
        return [move for move in self.character.moves if not move.super_art or move.super_art == self.super_art]

    def select_super_art(self, value: str) -> None:
        """Equip one of the character's Super Arts, as you would before a match.

        The buffer goes with it for the same reason :meth:`retune` clears it:
        what is sitting there was read against a different set of moves.
        """
        if value == self.super_art or value not in self.super_arts:
            return
        self.super_art = value
        self.recognizer = Recognizer(
            self._live_moves(), self.ruleset, decay_ms=self.recognizer.decay_ms, policy=self.recognizer.policy
        )
        self.buffer.clear()

    @property
    def direction(self) -> Direction:
        """The direction currently held."""
        return self.source.direction

    @property
    def gamepad_waiting(self) -> bool:
        """True when a gamepad layout is active but no pad is connected yet."""
        return self.gamepad is not None and not self.gamepad.connected

    @property
    def exact_input(self) -> bool:
        """Whether the terminal reports key releases, so holds are not guessed."""
        return self.source.exact_holds

    @property
    def hold_window_ms(self) -> int:
        """How long a single key press counts as a held direction."""
        return self.source.tap_ms

    @property
    def keyboard_advice(self) -> str:
        """Advice if the keyboard's repeat delay is hurting input timing."""
        if self.source.exact_holds:
            return ""  # Releases are reported, so the repeat delay is irrelevant.
        return repeat_delay_advice(self.source.repeat_delay_ms)

    def press(self, key: str, at_ms: int | None = None) -> bool:
        """Feed a key press in. Returns True when the display should redraw."""
        now = monotonic_ms() if at_ms is None else at_ms
        update = self.source.press(key, now)
        if update is None:
            return False

        self.total_inputs += 1
        if update.direction_changed:
            self.buffer.set_direction(update.direction, now)
            self._append_entry(update.direction, now)

        if update.button is None:
            return update.direction_changed

        self.buffer.press_button(update.button, now)
        self._record_button(update.button, update.direction, now)
        pressed = self.buffer.simultaneous_buttons(now)
        self.recognizer.decay_ms = self.source.decay_ms
        self._apply_activation(self.recognizer.evaluate(self.buffer, now, pressed))
        return True

    def _apply_activation(self, activation: Activation | None) -> bool:
        """Record a move the recogniser just produced. Returns True if it did."""
        if activation is None:
            return False
        self.activations.appendleft(activation)
        self.total_activations += 1
        for entry in reversed(self.entries):
            if entry.at_ms <= activation.at_ms:
                entry.activated = activation.name
                break
        return True

    def release(self, key: str, at_ms: int | None = None) -> bool:
        """Feed a key release in. Returns True when the display should redraw."""
        now = monotonic_ms() if at_ms is None else at_ms
        update = self.source.release(key, now)
        if update is None or not update.direction_changed:
            return False
        self.buffer.set_direction(update.direction, now)
        self._append_entry(update.direction, now)
        return True

    def tick(self, at_ms: int | None = None) -> bool:
        """Poll the gamepad and expire holds. Returns True if the display changed."""
        now = monotonic_ms() if at_ms is None else at_ms
        changed = self._poll_gamepad(now)
        update = self.source.tick(now)
        if update is not None and update.direction_changed:
            self.buffer.set_direction(update.direction, now)
            self._append_entry(update.direction, now)
            changed = True
        # A press held back for the rest of a multi-button input, whose other
        # buttons never came: let the lesser move on the motion through now.
        changed |= self._apply_activation(self.recognizer.poll(self.buffer, now))
        # A two-phase move whose follow-through taps never came: mark it missed.
        changed |= self.recognizer.advance_follow_up(now)
        return changed

    def _poll_gamepad(self, now: int) -> bool:
        """Feed any gamepad presses and releases through the normal path."""
        if self.gamepad is None:
            return False
        changed = False
        for code, pressed in self.gamepad.poll(now):
            if pressed:
                self.press(code, now)
            else:
                self.release(code, now)
            # Any pad event moves the panel display, even a button release, which
            # the engine itself treats as a no-op (buttons are momentary).
            changed = True
        return changed

    @property
    def policy(self) -> BufferPolicy:
        """Whether inputs are spent when a move comes out."""
        return self.recognizer.policy

    def rebind(self, layout: ControlLayout) -> None:
        """Take a changed control layout mid-session.

        Only the input display does this, when the player rearranges a panel
        from the settings. Everything held is dropped with the old bindings,
        since a key that meant one button a moment ago may mean another now.
        """
        self.layout = layout
        self.source.layout = layout
        self.reset()

    def retune(self, game: Game, policy: BufferPolicy) -> None:
        """Take changed rules mid-session, without losing the session.

        The buffer goes with them: what is in it was read under the old rules,
        and a half circle that has just stopped counting as one should not be
        left sitting there ready to come out.
        """
        self.game = game
        self.ruleset = game.ruleset
        self.recognizer.ruleset = game.ruleset
        self.recognizer.policy = policy
        self.buffer.clear()
        self.recognizer.reset()

    def reset(self) -> None:
        """Clear everything and go back to neutral."""
        self.buffer.clear()
        self.source.reset()
        if self.gamepad is not None:
            self.gamepad.reset()
        self.recognizer.reset()
        self.entries.clear()
        self.activations.clear()
        self.total_inputs = 0
        self.total_activations = 0

    def _append_entry(self, direction: Direction, at_ms: int) -> None:
        # Collapse a run of empty neutrals rather than filling the strip with them.
        previous = self.entries[-1] if self.entries else None
        if (
            direction is Direction.NEUTRAL
            and previous is not None
            and not previous.buttons
            and previous.direction is Direction.NEUTRAL
        ):
            return
        self.entries.append(InputEntry(direction=direction, at_ms=at_ms))

    def _record_button(self, button: Button, direction: Direction, at_ms: int) -> None:
        if self.entries:
            last = self.entries[-1]
            if last.direction is direction and at_ms - last.at_ms <= self.buffer.simultaneous_ms:
                last.buttons.append(button)
                return
        entry = InputEntry(direction=direction, at_ms=at_ms)
        entry.buttons.append(button)
        self.entries.append(entry)
