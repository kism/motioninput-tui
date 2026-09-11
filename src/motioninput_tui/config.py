"""Remembering the last used selection between runs.

Stored as JSON under the XDG config directory, which is
``~/.config/motioninput-tui/config.json`` unless ``XDG_CONFIG_HOME`` says
otherwise. Nothing here is essential: a missing, unreadable or corrupt file
just means the defaults are used, and a config that cannot be written is
logged and ignored rather than interrupting a training session.
"""

import json
import os
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from .controls.layouts import DEFAULT_LAYOUT, KEYBOARD_DEFAULT_BINDINGS, LAYOUTS
from .engine.recognizer import BufferPolicy
from .notation_styles import STYLES
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
    characters: dict[str, str] = field(default_factory=dict)
    """Who was last trained on each game, ``{game key: character key}``.
    :meth:`save` folds the current selection in, so coming back to a game comes
    back to the character as well."""
    layout: str = DEFAULT_LAYOUT
    buffer_policy: BufferPolicy = BufferPolicy.CONSUME
    neo_geo_slant: bool = False
    """Whether the Neo Geo's four buttons are arranged as the arcade slants
    them. See :mod:`motioninput_tui.controls.buttons`."""
    notation: dict[str, str] = field(default_factory=dict)
    """How each family of motions is written, ``{family: style}``. Empty means
    the plain default. See :mod:`motioninput_tui.notation_styles`."""
    gamepad_bindings: dict[str, str] = field(default_factory=dict)
    """The player's gamepad attack rebinds, ``{button name: pad code}``. Empty
    means the built-in default. :func:`~.controls.layouts.gamepad_layout` has
    the final say on which entries are usable."""
    keyboard_bindings: dict[str, str] = field(default_factory=dict)
    """The custom keyboard layout's rebinds, ``{slot: key name}`` over the four
    movement axes and the six attacks. Empty means the built-in default;
    :func:`~.controls.layouts.keyboard_layout` has the final say."""
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
            game=_valid_game(raw.get("game")),
            character=_optional_str(raw.get("character")),
            characters=_valid_characters(raw.get("characters")),
            layout=_valid_layout(raw.get("layout")),
            buffer_policy=_valid_policy(raw.get("buffer_policy")),
            neo_geo_slant=_valid_flag(raw.get("neo_geo_slant"), default=False),
            notation=_valid_notation(raw.get("notation")),
            gamepad_bindings=_valid_gamepad_bindings(raw.get("gamepad_bindings")),
            keyboard_bindings=_valid_keyboard_bindings(raw.get("keyboard_bindings")),
            path=target,
        )

    def save(self, path: Path | None = None) -> bool:
        """Write the config. Returns False if it could not be saved."""
        target = path or self.path or config_path()
        if self.game and self.character:
            self.characters[self.game] = self.character
        payload = {
            "game": self.game,
            "character": self.character,
            "characters": self.characters,
            "layout": self.layout,
            "buffer_policy": str(self.buffer_policy),
            "neo_geo_slant": self.neo_geo_slant,
            "notation": self.notation,
            "gamepad_bindings": self.gamepad_bindings,
            "keyboard_bindings": self.keyboard_bindings,
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


_LAYOUT_ALIASES = {"hitbox": "keyboard-left", "southpaw": "keyboard-right"}
"""The keyboard layouts that were replaced, mapped to their nearest successor so
a config from before the change still opens somewhere sensible."""

_GAME_ALIASES = {"lb2": "lastbld2", "ssii": "samsho2", "ssvsp": "samsh5sp"}
"""Games renamed to their MAME set names, so a config from before comes back to
the same game, and to the same character in it."""


def _valid_game(value: object) -> str | None:
    game = _optional_str(value)
    if game is None:
        return None
    return _GAME_ALIASES.get(game, game)


def _valid_layout(value: object) -> str:
    # An unavailable layout (gamepad without the extra installed) falls back,
    # so a stale config cannot drop the trainer into a dead input mode.
    if isinstance(value, str):
        value = _LAYOUT_ALIASES.get(value, value)
    if isinstance(value, str) and value in LAYOUTS and LAYOUTS[value].available:
        return value
    return DEFAULT_LAYOUT


def _valid_keyboard_bindings(value: object) -> dict[str, str]:
    # Best-effort like the rest of the loader; keyboard_layout is authoritative.
    if not isinstance(value, dict):
        return {}
    return {
        slot: key
        for slot, key in value.items()
        if isinstance(slot, str) and slot in KEYBOARD_DEFAULT_BINDINGS and isinstance(key, str) and key
    }


def _valid_characters(value: object) -> dict[str, str]:
    # Best-effort like the rest of the loader; a character who has since left
    # the roster is dealt with by the picker falling back to the first one.
    if not isinstance(value, dict):
        return {}
    return {
        _GAME_ALIASES.get(game, game): character
        for game, character in value.items()
        if isinstance(game, str) and game and isinstance(character, str) and character
    }


def _valid_flag(value: object, *, default: bool) -> bool:
    """A saved on/off, ignoring anything that is not one."""
    return value if isinstance(value, bool) else default


def _valid_policy(value: object) -> BufferPolicy:
    try:
        return BufferPolicy(value)
    except ValueError:
        return BufferPolicy.CONSUME


def _valid_notation(value: object) -> dict[str, str]:
    # Styles come and go as the notation menu grows, so an entry naming one
    # that is not there any more is dropped rather than left to draw nothing.
    if not isinstance(value, dict):
        return {}
    known = {family.value: {style.key for style in styles} for family, styles in STYLES.items()}
    return {
        family: style
        for family, style in value.items()
        if isinstance(family, str) and isinstance(style, str) and style in known.get(family, ())
    }


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
