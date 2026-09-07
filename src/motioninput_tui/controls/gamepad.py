"""Reading a gamepad for the gamepad control layout.

pygame is an optional dependency (the ``gamepad`` extra). Everything here
degrades to "no gamepad" when it is missing or nothing is plugged in, so the
rest of the trainer never has to care.

The pad is read through SDL's *game controller* API, not the raw joystick one,
so buttons mean the same thing on every pad: SDL's controller database maps
each device's real button numbering onto the Xbox-style A/B/X/Y/LB/RB/triggers
layout. (Reading raw joystick buttons breaks on pads whose firmware numbers
them oddly, which is most of them.)

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

TRIGGER_THRESHOLD = 0.5
"""How far a trigger must be pulled before it counts as a button press."""

# SDL2 ``SDL_GameControllerButton`` / ``...Axis`` enum values. These are part of
# SDL's stable ABI; pygame also exposes them as ``pygame.CONTROLLER_BUTTON_*``.
# Naming them here keeps :func:`codes_from_pad` a plain function the tests can
# drive without pygame.
_BUTTON_A, _BUTTON_B, _BUTTON_X, _BUTTON_Y = 0, 1, 2, 3
_BUTTON_LEFTSHOULDER, _BUTTON_RIGHTSHOULDER = 9, 10
_BUTTON_DPAD_UP, _BUTTON_DPAD_DOWN, _BUTTON_DPAD_LEFT, _BUTTON_DPAD_RIGHT = 11, 12, 13, 14
_AXIS_LEFTX, _AXIS_LEFTY = 0, 1
_AXIS_TRIGGERLEFT, _AXIS_TRIGGERRIGHT = 4, 5

# Which pad control each ``pad:*`` attack code comes from. ``pad:0``..``pad:5``
# are the face and shoulder buttons; ``pad:6``/``pad:7`` are the triggers.
_ATTACK_BUTTONS: dict[int, str] = {
    _BUTTON_A: "pad:0",
    _BUTTON_B: "pad:1",
    _BUTTON_X: "pad:2",
    _BUTTON_Y: "pad:3",
    _BUTTON_LEFTSHOULDER: "pad:4",
    _BUTTON_RIGHTSHOULDER: "pad:5",
}
_ATTACK_TRIGGERS: dict[int, str] = {_AXIS_TRIGGERLEFT: "pad:6", _AXIS_TRIGGERRIGHT: "pad:7"}
_DPAD_DIRECTIONS: dict[int, str] = {
    _BUTTON_DPAD_LEFT: "pad:left",
    _BUTTON_DPAD_RIGHT: "pad:right",
    _BUTTON_DPAD_UP: "pad:up",
    _BUTTON_DPAD_DOWN: "pad:down",
}


class Pad(Protocol):
    """The slice of ``pygame._sdl2.controller.Controller`` this module uses."""

    @property
    def name(self) -> str: ...
    def get_button(self, button: int) -> int: ...
    def get_axis(self, axis: int) -> float: ...


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
        from pygame._sdl2 import controller  # ruff: ignore[import-outside-top-level,import-private-name] - the only game-controller API pygame exposes
    except ImportError:
        logger.info("pygame is not installed; the gamepad layout is unavailable")
        return None
    try:
        pygame.display.init()
        pygame.joystick.init()
        controller.init()
    except pygame.error:
        logger.warning("Could not initialise pygame for gamepad input", exc_info=True)
        return None
    return pygame


def _first_controller(pygame: ModuleType) -> Pad | None:
    """Open the first plugged-in device SDL recognises as a game controller."""
    from pygame._sdl2 import controller  # ruff: ignore[import-outside-top-level,import-private-name] - see _load_pygame

    for index in range(controller.get_count()):
        if not controller.is_controller(index):
            continue
        try:
            return controller.Controller(index)
        except pygame.error:
            logger.warning("Could not open the gamepad", exc_info=True)
            return None
    return None


def codes_from_pad(pad: Pad, deadzone: float = AXIS_DEADZONE) -> frozenset[str]:
    """The binding codes a pad's current state maps to.

    The d-pad and the left stick both drive movement. SDL reports stick-down as
    +y, so the down/up test is on the sign of ``y`` directly.
    """
    codes: set[str] = {code for button, code in _ATTACK_BUTTONS.items() if pad.get_button(button)}
    codes.update(code for axis, code in _ATTACK_TRIGGERS.items() if pad.get_axis(axis) >= TRIGGER_THRESHOLD)
    codes.update(code for button, code in _DPAD_DIRECTIONS.items() if pad.get_button(button))

    x, y = pad.get_axis(_AXIS_LEFTX), pad.get_axis(_AXIS_LEFTY)
    if x <= -deadzone:
        codes.add("pad:left")
    if x >= deadzone:
        codes.add("pad:right")
    if y >= deadzone:
        codes.add("pad:down")
    if y <= -deadzone:
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
        self._pad: Pad | None = None
        self._held: frozenset[str] = frozenset()

    @property
    def available(self) -> bool:
        """Whether gamepad input is possible at all (pygame is installed)."""
        return self._pygame is not None

    @property
    def connected(self) -> bool:
        """Whether a pad is currently open."""
        return self._pad is not None

    @property
    def name(self) -> str | None:
        """The open pad's name as SDL reports it, or None if none is open.

        SDL often reports a generic name (just "Controller" on macOS); the
        caller decides what to show when this is empty.
        """
        pygame = self._pygame
        if self._pad is None or pygame is None:
            return None
        try:
            return self._pad.name or None
        except pygame.error:
            logger.warning("Could not read the gamepad name", exc_info=True)
            return None

    def poll(self, at_ms: int) -> list[tuple[str, bool]]:
        """Advance pygame and return press/release events since the last poll."""
        del at_ms  # A gamepad event is exact; there is no timing to learn.
        pygame = self._pygame
        if pygame is None:
            return []
        pygame.event.pump()
        if self._pad is None:
            self._open()

        current: frozenset[str] = frozenset()
        if self._pad is not None:
            try:
                current = codes_from_pad(self._pad, self.deadzone)
            except pygame.error:
                logger.warning("Lost the gamepad", exc_info=True)
                self._pad = None

        events = diff_codes(self._held, current)
        self._held = current
        return events

    def reset(self) -> None:
        """Forget which inputs are held, so any still down re-press next poll."""
        self._held = frozenset()

    def _open(self) -> None:
        if self._pygame is None:
            return
        self._pad = _first_controller(self._pygame)
        if self._pad is not None:
            logger.info("Gamepad connected: %s", self._pad.name)

    def __rich_repr__(self) -> Iterable[tuple[str, object]]:  # ruff: ignore[bad-dunder-method-name] - Rich's repr protocol
        """Debug representation."""
        yield "available", self.available
        yield "connected", self.connected
