"""Remembering the last used selection between runs.

Stored as JSON under the XDG config directory, which is
``~/.config/motioninput-tui/config.json`` unless ``XDG_CONFIG_HOME`` says
otherwise. Nothing here is essential: a missing, unreadable or corrupt file
just means the defaults are used, and a config that cannot be written is
logged and ignored rather than interrupting a training session.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from .controls.layouts import DEFAULT_LAYOUT, LAYOUTS
from .engine.recognizer import BufferPolicy
from .utils.logger import get_logger

logger = get_logger(__name__)

APP_DIR_NAME = "motioninput-tui"
CONFIG_FILENAME = "config.json"


def config_dir() -> Path:
    """The directory holding the config file."""
    override = os.environ.get("XDG_CONFIG_HOME")
    base = Path(override).expanduser() if override else Path.home() / ".config"
    return base / APP_DIR_NAME


def config_path() -> Path:
    """The config file itself."""
    return config_dir() / CONFIG_FILENAME


@dataclass(slots=True)
class Config:
    """What the trainer remembers between runs.

    ``key_release`` is deliberately not stored. It is probed per terminal on
    every launch, so remembering it would disable exact tracking after moving
    to a different terminal.
    """

    game: str | None = None
    character: str | None = None
    layout: str = DEFAULT_LAYOUT
    buffer_policy: BufferPolicy = BufferPolicy.CONSUME
    lenient_half_circles: bool = True
    """Whether a half circle may skip straight down. See
    :mod:`motioninput_tui.settings`."""
    gamepad_bindings: dict[str, str] = field(default_factory=dict)
    """The player's gamepad attack rebinds, ``{button name: pad code}``. Empty
    means the built-in default. :func:`~.controls.layouts.gamepad_layout` has
    the final say on which entries are usable."""
    path: Path | None = None
    """Where this was loaded from, and where :meth:`save` writes back to."""

    @property
    def loose_buffer(self) -> bool:
        """The buffer policy as a plain on/off, which is how it is presented.

        The settings pane treats every setting as a boolean attribute, and
        ``buffer_policy`` is the one that is really an enum, so it is bridged
        here rather than special cased there.
        """
        return self.buffer_policy is BufferPolicy.LOOSE

    @loose_buffer.setter
    def loose_buffer(self, on: bool) -> None:
        self.buffer_policy = BufferPolicy.LOOSE if on else BufferPolicy.CONSUME

    @classmethod
    def load(cls, path: Path | None = None) -> Config:
        """Read the saved config, falling back to defaults on any problem."""
        target = path or config_path()
        try:
            with target.open(encoding="utf-8") as handle:
                raw = json.load(handle)
        except FileNotFoundError:
            return cls(path=target)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Ignoring unreadable config at %s: %s", target, exc)
            return cls(path=target)

        if not isinstance(raw, dict):
            logger.warning("Ignoring config at %s: expected an object", target)
            return cls(path=target)
        return cls(
            game=_optional_str(raw.get("game")),
            character=_optional_str(raw.get("character")),
            layout=_valid_layout(raw.get("layout")),
            buffer_policy=_valid_policy(raw.get("buffer_policy")),
            lenient_half_circles=_valid_flag(raw.get("lenient_half_circles"), default=True),
            gamepad_bindings=_valid_gamepad_bindings(raw.get("gamepad_bindings")),
            path=target,
        )

    def save(self, path: Path | None = None) -> bool:
        """Write the config. Returns False if it could not be saved."""
        target = path or self.path or config_path()
        payload = {
            "game": self.game,
            "character": self.character,
            "layout": self.layout,
            "buffer_policy": str(self.buffer_policy),
            "lenient_half_circles": self.lenient_half_circles,
            "gamepad_bindings": self.gamepad_bindings,
        }
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            _write_atomic(target, json.dumps(payload, indent=2) + "\n")
        except OSError as exc:
            logger.warning("Could not save config to %s: %s", target, exc)
            return False
        logger.debug("Saved config to %s", target)
        return True


def _write_atomic(target: Path, text: str) -> None:
    """Write via a temporary file so an interrupted run cannot truncate it."""
    handle = tempfile.NamedTemporaryFile(  # ruff: ignore[open-file-with-context-handler] - closed before the rename
        "w",
        encoding="utf-8",
        dir=target.parent,
        prefix=f".{target.name}.",
        delete=False,
    )
    temporary = Path(handle.name)
    try:
        with handle:
            handle.write(text)
        temporary.replace(target)
    except OSError:
        temporary.unlink(missing_ok=True)
        raise


def _optional_str(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _valid_layout(value: object) -> str:
    # An unavailable layout (gamepad without the extra installed) falls back,
    # so a stale config cannot drop the trainer into a dead input mode.
    if isinstance(value, str) and value in LAYOUTS and LAYOUTS[value].available:
        return value
    return DEFAULT_LAYOUT


def _valid_flag(value: object, *, default: bool) -> bool:
    """A saved on/off, ignoring anything that is not one."""
    return value if isinstance(value, bool) else default


def _valid_policy(value: object) -> BufferPolicy:
    try:
        return BufferPolicy(value)
    except ValueError:
        return BufferPolicy.CONSUME


_PAD_CODE = re.compile(r"^pad:\d+$")


def _valid_gamepad_bindings(value: object) -> dict[str, str]:
    # Best-effort, like the rest of the loader: keep the entries that look sane
    # and drop the rest. gamepad_layout does the authoritative check.
    if not isinstance(value, dict):
        return {}
    return {
        key: code
        for key, code in value.items()
        if isinstance(key, str) and isinstance(code, str) and _PAD_CODE.match(code)
    }
