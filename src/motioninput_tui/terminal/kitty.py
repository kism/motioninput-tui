"""The kitty keyboard protocol, which is how a terminal can report key releases.

Ordinary terminals only ever tell you a key went down. The kitty keyboard
protocol adds an event type to each key report, so a key can be tracked exactly
the way a gamepad would be, with no guessing about when the player let go.

Terminals implementing it include kitty, Ghostty, foot, WezTerm, Alacritty,
Contour and Rio. Anywhere it is missing the trainer falls back to inferring
holds from auto-repeat, so this is a progressive enhancement rather than a
requirement.

Reference: https://sw.kovidgoyal.net/kitty/keyboard-protocol/
"""

import os
import re
import select
import sys
import time
from enum import IntEnum
from typing import Final

if sys.platform != "win32":
    import termios
    import tty

DISAMBIGUATE_ESCAPE_CODES: Final = 0b00001
REPORT_EVENT_TYPES: Final = 0b00010
REPORT_ALTERNATE_KEYS: Final = 0b00100
REPORT_ALL_KEYS: Final = 0b01000
REPORT_ASSOCIATED_TEXT: Final = 0b10000

RELEASE_FLAGS: Final = DISAMBIGUATE_ESCAPE_CODES | REPORT_EVENT_TYPES | REPORT_ALL_KEYS | REPORT_ASSOCIATED_TEXT
"""What we need for exact key tracking. REPORT_ALL_KEYS is what makes ordinary
letter keys report at all; REPORT_EVENT_TYPES is what distinguishes down from up."""


def set_flags(flags: int = RELEASE_FLAGS) -> str:
    """Escape sequence setting the protocol flags of the current stack entry.

    Uses the 'set' form rather than the 'push' form, so it modifies whatever
    entry the host application already pushed instead of adding another one.
    That leaves the host's own pop (``CSI < u``) correct on exit.
    """
    return f"\x1b[={flags};1u"


class EventType(IntEnum):
    """The event type field of a key report."""

    PRESS = 1
    REPEAT = 2
    RELEASE = 3


# CSI <codes> <terminator>, where codes are semicolon separated fields that may
# each carry colon separated sub-parameters.
_KEY_REPORT = re.compile(r"\x1b\[([\d:;]*)([u~ABCDEFHPQRS])")

MODIFIER_FIELD = 1
"""Field index carrying 'modifiers:event-type'."""


def split_event_type(sequence: str) -> tuple[str, EventType] | None:
    """Separate a key report's event type from the rest of the sequence.

    Returns the sequence with the event type removed, so it reads like an
    ordinary key report, plus the event type itself. Returns None when the
    sequence is not a key report or carries no event type, in which case the
    caller should handle it as it always would.
    """
    match = _KEY_REPORT.fullmatch(sequence)
    if match is None:
        return None

    codes, terminator = match.groups()
    fields = codes.split(";")
    if len(fields) <= MODIFIER_FIELD or ":" not in fields[MODIFIER_FIELD]:
        return None

    modifiers, _, raw_event = fields[MODIFIER_FIELD].partition(":")
    try:
        event_type = EventType(int(raw_event))
    except ValueError:
        return None

    fields[MODIFIER_FIELD] = modifiers or "1"
    return f"\x1b[{';'.join(fields)}{terminator}", event_type


QUERY = "\x1b[?u"
"""Ask the terminal which protocol flags it supports."""

_PRIMARY_DEVICE_ATTRIBUTES = "\x1b[c"
"""Sent after the query as a barrier: every terminal answers this one, so a
reply to it without a reply to the query means the protocol is unsupported."""

_QUERY_REPLY = re.compile(r"\x1b\[\?\d+u")
_BARRIER_REPLY = re.compile(r"\x1b\[\?[\d;]*c")


def query_support(timeout: float = 0.3) -> bool | None:
    """Ask the terminal whether it speaks the kitty keyboard protocol.

    Returns True or False, or None when there is no terminal to ask (piped
    output, or a platform without termios). Safe to call before the interface
    starts; it restores the terminal settings it changes.
    """
    if sys.platform == "win32":  # pragma: no cover - no termios, no kitty protocol
        return None
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        return None

    fd = sys.stdin.fileno()
    try:
        original = termios.tcgetattr(fd)
    except termios.error:  # pragma: no cover - not a real terminal
        return None

    try:
        tty.setraw(fd)
        sys.stdout.write(QUERY + _PRIMARY_DEVICE_ATTRIBUTES)
        sys.stdout.flush()
        return _QUERY_REPLY.search(_read_reply(fd, timeout)) is not None
    except OSError, termios.error:  # pragma: no cover - terminal went away
        return None
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, original)


def _read_reply(fd: int, timeout: float) -> str:
    """Collect terminal replies until the barrier answers or time runs out."""
    reply = ""
    deadline = time.monotonic() + timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return reply
        readable, _, _ = select.select([fd], [], [], remaining)
        if not readable:
            return reply
        reply += os.read(fd, 128).decode("utf-8", errors="replace")
        if _BARRIER_REPLY.search(reply):
            return reply
