"""Gamepad diagnostic: dump what SDL reports for the connected pad.

Run it, then work the stick and every button. Each state change is recorded
three ways: the raw joystick view, SDL's game-controller view, and the binding
codes the trainer would actually see. Stop with ctrl+c (or ``--seconds``). A
datestamped copy of the whole session, named after the pad, is written to
``/tmp`` so it can be pasted into a bug report.

    python -m motioninput_tui.gamepad_probe
    python -m motioninput_tui.gamepad_probe --seconds 30
"""

from __future__ import annotations

import argparse
import contextlib
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from .constants import PROGRAM_NAME
from .controls.gamepad import AXIS_DEADZONE, AXIS_MAX, TRIGGER_THRESHOLD, codes_from_pad, load_pygame
from .utils.logger import get_logger, setup_logger_cli

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from types import ModuleType

    from .controls.gamepad import Pad

logger = get_logger(__name__)


class RawJoystick(Protocol):
    """The slice of ``pygame.joystick.Joystick`` this diagnostic reads."""

    def get_name(self) -> str: ...
    def get_guid(self) -> str: ...
    def get_numbuttons(self) -> int: ...
    def get_button(self, index: int) -> bool: ...
    def get_numaxes(self) -> int: ...
    def get_axis(self, index: int) -> float: ...
    def get_numhats(self) -> int: ...
    def get_hat(self, index: int) -> tuple[int, int]: ...


_REPORT_DIR = Path("/tmp")  # ruff: ignore[hardcoded-temp-file] - a diagnostic dump the user wants to find in /tmp
_POLL_SECONDS = 0.02
_SHOW_AXIS_ABOVE = 0.35
"""Axes quieter than this are resting noise; do not clutter the report."""

_BUTTON_KEYS = [
    "A",
    "B",
    "X",
    "Y",
    "BACK",
    "GUIDE",
    "START",
    "LEFTSTICK",
    "RIGHTSTICK",
    "LEFTSHOULDER",
    "RIGHTSHOULDER",
    "DPAD_UP",
    "DPAD_DOWN",
    "DPAD_LEFT",
    "DPAD_RIGHT",
]
_AXIS_KEYS = ["LEFTX", "LEFTY", "RIGHTX", "RIGHTY", "TRIGGERLEFT", "TRIGGERRIGHT"]


def _slug(name: str) -> str:
    """A filename-safe version of the pad's name."""
    return re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-") or "pad"


def _report_path(name: str) -> Path:
    """Where this session's dump is written: /tmp, datestamped, pad-named."""
    return _REPORT_DIR / f"{PROGRAM_NAME}-gamepad-probe_{_slug(name)}_{datetime.now():%Y%m%d-%H%M%S}.txt"


def _wait_for_pad(pygame: ModuleType) -> bool:
    """Give a pad a moment to enumerate; True once one has."""
    for _ in range(40):
        pygame.event.pump()
        if pygame.joystick.get_count():
            return True
        time.sleep(0.05)
    return False


def _describe(
    joystick: RawJoystick, pad: Pad | None, mapping: dict[str, str] | None, record: Callable[[str], None]
) -> None:
    """The static header: identity, counts, and SDL's mapping."""
    record(f"{PROGRAM_NAME} gamepad probe   {datetime.now():%Y-%m-%d %H:%M:%S}")
    record(f"device          {joystick.get_name()!r}")
    record(f"guid            {joystick.get_guid()}")
    record(
        f"raw counts      buttons={joystick.get_numbuttons()} "
        f"axes={joystick.get_numaxes()} hats={joystick.get_numhats()}"
    )
    record(f"is_controller   {pad is not None}")
    record(f"thresholds      stick +-{AXIS_DEADZONE}   trigger {TRIGGER_THRESHOLD}")
    if mapping is not None:
        record("SDL controller mapping:")
        for key, value in sorted(mapping.items()):
            record(f"    {key:>16} = {value}")
    else:
        record("!! SDL does not recognise this device as a game controller.")
        record("!! The trainer reads pads through the controller API, so it sees nothing.")
    record("")
    record("Work the stick and every button now. ctrl+c to finish.")
    record("")


def _snapshot(joystick: RawJoystick, pad: Pad | None, buttons: Mapping[int, str], axes: Mapping[int, str]) -> str:
    """One line describing everything currently pressed."""
    held_b = [b for b in range(joystick.get_numbuttons()) if joystick.get_button(b)]
    loud_a = [
        f"a{a}={joystick.get_axis(a):+.2f}"
        for a in range(joystick.get_numaxes())
        if abs(joystick.get_axis(a)) > _SHOW_AXIS_ABOVE
    ]
    held_h = [joystick.get_hat(h) for h in range(joystick.get_numhats())]
    parts = [f"raw: buttons={held_b} axes={loud_a} hats={held_h}"]
    if pad is not None:
        pressed = [name for button, name in buttons.items() if pad.get_button(button)]
        # Controller axes come back as raw int16; scale to match codes_from_pad.
        loud = [
            f"{name}={pad.get_axis(axis) / AXIS_MAX:+.2f}"
            for axis, name in axes.items()
            if abs(pad.get_axis(axis) / AXIS_MAX) > _SHOW_AXIS_ABOVE
        ]
        parts += [
            f"controller: buttons={pressed} axes={loud}",
            f"trainer sees: {sorted(codes_from_pad(pad))}",
        ]
    return "   |   ".join(parts)


def _poll_loop(
    pygame: ModuleType,
    joystick: RawJoystick,
    pad: Pad | None,
    record: Callable[[str], None],
    deadline: float | None,
) -> None:
    buttons = {int(getattr(pygame, f"CONTROLLER_BUTTON_{k}")): k for k in _BUTTON_KEYS}
    axes = {int(getattr(pygame, f"CONTROLLER_AXIS_{k}")): k for k in _AXIS_KEYS}
    last = ""
    while deadline is None or time.monotonic() < deadline:
        pygame.event.pump()
        line = _snapshot(joystick, pad, buttons, axes)
        if line != last:
            record(line)
            last = line
        time.sleep(_POLL_SECONDS)


def _watch(
    pygame: ModuleType, joystick: RawJoystick, pad: Pad | None, record: Callable[[str], None], *, seconds: float
) -> None:
    """Poll until ctrl+c (or ``seconds`` elapse), recording every change."""
    deadline = time.monotonic() + seconds if seconds else None
    with contextlib.suppress(KeyboardInterrupt):
        _poll_loop(pygame, joystick, pad, record, deadline)
    record("")
    record("stopped")


def main() -> int:
    """Entry point for ``python -m motioninput_tui.gamepad_probe``."""
    parser = argparse.ArgumentParser(prog=f"{PROGRAM_NAME}.gamepad_probe", description=__doc__)
    parser.add_argument("--seconds", type=float, default=0.0, help="Stop after this long instead of on ctrl+c.")
    parser.add_argument("-v", action="count", default=0, help="Increase verbosity.")
    args = parser.parse_args()
    setup_logger_cli(args.v)

    pygame = load_pygame()
    if pygame is None:
        logger.error("pygame is not available. Install the gamepad extra: uv sync --extra gamepad")
        return 1

    from pygame._sdl2 import controller  # ruff: ignore[import-outside-top-level,import-private-name] - the only game-controller API pygame exposes

    if not _wait_for_pad(pygame):
        logger.error("No gamepad detected. Plug one in and try again.")
        return 1

    joystick = pygame.joystick.Joystick(0)
    pad = controller.Controller(0) if controller.is_controller(0) else None
    mapping = pad.get_mapping() if pad is not None else None

    lines: list[str] = []

    def record(text: str) -> None:
        logger.info("%s", text)
        lines.append(text)

    _describe(joystick, pad, mapping, record)
    _watch(pygame, joystick, pad, record, seconds=args.seconds)

    path = _report_path(joystick.get_name())
    try:
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except OSError as exc:
        logger.error("Could not write the report to %s: %s", path, exc)  # ruff: ignore[error-instead-of-exception] - a traceback helps nobody here
        return 1
    logger.info("Wrote %s", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
