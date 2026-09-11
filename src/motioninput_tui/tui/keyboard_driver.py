"""A Textual driver that also reports key releases.

Textual asks the terminal for the kitty keyboard protocol but not for event
types, and its parser raises on the ``modifiers:event-type`` field, so key
releases never reach an application. This driver asks for event types as well
and understands the replies.

Two pieces of Textual's internals are touched: the escape sequence written in
``start_application_mode``, and the parser class used by the input thread. Both
are guarded, and if either stops working the trainer simply falls back to
inferring holds from auto-repeat.
"""

import logging
import sys
from typing import TYPE_CHECKING

from textual import events
from textual._xterm_parser import XTermParser  # ruff: ignore[import-private-name] - no public parser hook exists
from textual.drivers.linux_driver import LinuxDriver

from motioninput_tui.terminal.kitty import EventType, set_flags, split_event_type

if TYPE_CHECKING:
    from collections.abc import Iterable

logger = logging.getLogger(__name__)

_PARSER_ATTR = "XTermParser"


class KeyRelease(events.Event):
    """A key going back up.

    Deliberately not a subclass of :class:`textual.events.Key`, so that Textual
    does not route it to the focused widget or fire the binding a second time.
    """

    def __init__(self, key: str) -> None:
        """Record which key was released."""
        super().__init__()
        self.key = key

    def copy(self) -> KeyRelease:
        """A fresh copy. Textual copies parsed events before dispatching them."""
        return KeyRelease(self.key)

    def __rich_repr__(self) -> Iterable[tuple[str, str]]:  # ruff: ignore[bad-dunder-method-name] - Rich's repr protocol
        """Debug representation."""
        yield "key", self.key


class ReleaseAwareParser(XTermParser):
    """Parses key reports that carry an event type.

    Presses and auto-repeats are handed to Textual unchanged; releases become
    :class:`KeyRelease` events instead.
    """

    # Textual caches this method with lru_cache. The override is deliberately
    # uncached so that every release builds a fresh event rather than handing
    # the same Message object out twice.
    def _parse_extended_key(self, sequence: str) -> list[events.Key] | None:  # ty: ignore[invalid-method-override]
        split = split_event_type(sequence)
        if split is None:
            return super()._parse_extended_key(sequence)

        cleaned, event_type = split
        keys = super()._parse_extended_key(cleaned)
        if keys is None or event_type is not EventType.RELEASE:
            return keys
        # Runtime only cares that these are events; the annotation is Textual's.
        return [KeyRelease(key.key) for key in keys]  # ty: ignore[invalid-return-type]


class ReleaseAwareDriver(LinuxDriver):
    """Linux/macOS driver that asks the terminal to report key releases."""

    def start_application_mode(self) -> None:
        """Enter application mode, then ask for key event types as well."""
        super().start_application_mode()
        try:
            self.write(set_flags())
            self.flush()
        except OSError:
            logger.warning("Could not enable kitty key release reporting", exc_info=True)

    def run_input_thread(self) -> None:
        """Run Textual's input loop with a parser that understands releases.

        Textual builds its parser inside this method, so the class is swapped
        for the lifetime of the thread rather than the loop being duplicated
        here. The replacement is a strict superset of Textual's own parser.
        """
        module = sys.modules.get(LinuxDriver.__module__)
        if module is None or getattr(module, _PARSER_ATTR, None) is not XTermParser:
            logger.warning("Textual's input parser could not be replaced; key releases unavailable")
            super().run_input_thread()
            return

        setattr(module, _PARSER_ATTR, ReleaseAwareParser)
        try:
            super().run_input_thread()
        finally:
            setattr(module, _PARSER_ATTR, XTermParser)
