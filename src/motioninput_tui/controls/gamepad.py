"""Reading a gamepad for the gamepad control layout.

pygame is an optional dependency (the ``gamepad`` extra). Everything here
degrades to "no gamepad" when it is missing or nothing is plugged in, so the
rest of the trainer never has to care.

Unlike a terminal, a gamepad reports releases, so holds are exact and there is
nothing to infer. The training tick polls :class:`GamepadReader`, which diffs
the pad's state and returns press and release events keyed by the same binding
codes the :data:`~.layouts.GAMEPAD` layout uses (``pad:left``, ``pad:0`` ...).
"""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING, Protocol

from motioninput_tui.utils.logger import get_logger

if TYPE_CHECKING:
    from collections.abc import Iterable
    from types import ModuleType

logger = get_logger(__name__)

AXIS_DEADZONE = 0.5
"""How far the stick must move off centre before it counts as a direction."""

_MAX_BUTTONS = 6
"""Only the first six buttons are bound; the rest are start/select/sticks."""

_LEFT_STICK_AXES = 2
"""Axes 0 and 1 are the left stick; a pad with fewer has no analogue stick."""


class Joystick(Protocol):
    """The slice of ``pygame.joystick.Joystick`` this module uses."""

    def init(self) -> None: ...
    def get_name(self) -> str: ...
    def get_numbuttons(self) -> int: ...
    def get_button(self, index: int) -> bool: ...
    def get_numaxes(self) -> int: ...
    def get_axis(self, index: int) -> float: ...
    def get_numhats(self) -> int: ...
    def get_hat(self, index: int) -> tuple[int, int]: ...


def _load_pygame() -> ModuleType | None:
    """Import pygame headlessly, or return None if the extra is not installed.

    On macOS the SDL joystick subsystem only sees gamepads when the real Cocoa
    video driver is initialised (the ``dummy`` driver reports none); the
    background-app hint keeps that from stealing focus or a Dock icon from the
    TUI. Everywhere else the dummy driver is enough and avoids needing a
    display at all.
    """
    if sys.platform == "darwin":
        os.environ.setdefault("SDL_MAC_BACKGROUND_APP", "1")
    else:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    try:
        import pygame  # ruff: ignore[import-outside-top-level] - optional dependency, only when a gamepad is used
    except ImportError:
        logger.info("pygame is not installed; the gamepad layout is unavailable")
        return None
    try:
        pygame.display.init()
        pygame.joystick.init()
    except pygame.error:
        logger.warning("Could not initialise pygame for gamepad input", exc_info=True)
        return None
    return pygame


def codes_from_joystick(joystick: Joystick, deadzone: float = AXIS_DEADZONE) -> frozenset[str]:
    """The binding codes a joystick's current state maps to.

    The d-pad (hat 0) and the left stick (axes 0 and 1) both drive movement.
    SDL reports stick-down as +y and hat-up as +y, hence the sign flip.
    """
    codes: set[str] = set()
    for index in range(min(joystick.get_numbuttons(), _MAX_BUTTONS)):
        if joystick.get_button(index):
            codes.add(f"pad:{index}")

    x = y = 0.0
    if joystick.get_numaxes() >= _LEFT_STICK_AXES:
        x, y = joystick.get_axis(0), joystick.get_axis(1)
    hat_x = hat_y = 0
    if joystick.get_numhats() >= 1:
        hat_x, hat_y = joystick.get_hat(0)

    if x <= -deadzone or hat_x < 0:
        codes.add("pad:left")
    if x >= deadzone or hat_x > 0:
        codes.add("pad:right")
    if y >= deadzone or hat_y < 0:
        codes.add("pad:down")
    if y <= -deadzone or hat_y > 0:
        codes.add("pad:up")
    return frozenset(codes)


def diff_codes(previous: frozenset[str], current: frozenset[str]) -> list[tuple[str, bool]]:
    """Press/release events to get from one set of held codes to another.

    Releases come first, so a direction that flips (back to forward) is let go
    of before the new one is pressed.
    """
    events: list[tuple[str, bool]] = [(code, False) for code in previous - current]
    events.extend((code, True) for code in current - previous)
    return events


class GamepadReader:
    """Polls the first connected gamepad and reports what changed.

    Cheap to construct and safe when pygame is missing or nothing is plugged
    in: :meth:`poll` just returns no events. The pad is opened lazily on the
    first poll that sees one, so plugging in after launch works.
    """

    def __init__(self, deadzone: float = AXIS_DEADZONE) -> None:
        """Set up polling; does not open a pad yet."""
        self.deadzone = deadzone
        self._pygame = _load_pygame()
        self._joystick: Joystick | None = None
        self._held: frozenset[str] = frozenset()

    @property
    def available(self) -> bool:
        """Whether gamepad input is possible at all (pygame is installed)."""
        return self._pygame is not None

    @property
    def connected(self) -> bool:
        """Whether a pad is currently open."""
        return self._joystick is not None

    def poll(self, at_ms: int) -> list[tuple[str, bool]]:
        """Advance pygame and return press/release events since the last poll."""
        del at_ms  # A gamepad event is exact; there is no timing to learn.
        pygame = self._pygame
        if pygame is None:
            return []
        pygame.event.pump()
        if self._joystick is None:
            self._open(pygame)

        current: frozenset[str] = frozenset()
        if self._joystick is not None:
            try:
                current = codes_from_joystick(self._joystick, self.deadzone)
            except pygame.error:
                logger.warning("Lost the gamepad", exc_info=True)
                self._joystick = None

        events = diff_codes(self._held, current)
        self._held = current
        return events

    def reset(self) -> None:
        """Forget which inputs are held, so any still down re-press next poll."""
        self._held = frozenset()

    def _open(self, pygame: ModuleType) -> None:
        if pygame.joystick.get_count() == 0:
            return
        try:
            joystick = pygame.joystick.Joystick(0)
            joystick.init()
        except pygame.error:
            logger.warning("Could not open the gamepad", exc_info=True)
            return
        self._joystick = joystick
        logger.info("Gamepad connected: %s", joystick.get_name())

    def __rich_repr__(self) -> Iterable[tuple[str, object]]:  # ruff: ignore[bad-dunder-method-name] - Rich's repr protocol
        """Debug representation."""
        yield "available", self.available
        yield "connected", self.connected
