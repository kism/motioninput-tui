"""Physical control layouts.

Everything downstream talks to :class:`ControlLayout`. Keyboard layouts bind
literal key names; the gamepad layout binds ``pad:*`` codes that
:mod:`motioninput_tui.controls.gamepad` produces from the pad's state.
"""

import importlib.util
from dataclasses import dataclass, field, replace
from enum import StrEnum
from typing import TYPE_CHECKING

from motioninput_tui.engine.notation import BUTTON_ORDER, Button

from .buttons import DEFAULT_SET, ButtonSet

if TYPE_CHECKING:
    from collections.abc import Mapping


class Axis(StrEnum):
    """One of the four movement inputs."""

    LEFT = "left"
    RIGHT = "right"
    DOWN = "down"
    UP = "up"


_KEY_DISPLAY = {
    "space": "␣",
    "comma": ",",
    "semicolon": ";",
    "full_stop": ".",
    "minus": "-",
    "slash": "/",
    "apostrophe": "'",
    "left_square_bracket": "[",
    "right_square_bracket": "]",
}
"""Friendly one-glyph names for the keys Textual reports under a word."""


def friendly_key(key: str) -> str:
    """A key name as it should read on screen, e.g. ``comma`` -> ``,``."""
    return _KEY_DISPLAY.get(key, key)


class LayoutKind(StrEnum):
    """The device family a layout is for."""

    KEYBOARD = "keyboard"
    GAMEPAD = "gamepad"


@dataclass(frozen=True, slots=True)
class ControlLayout:
    """A mapping from physical inputs to directions and attack buttons.

    ``attack_rows`` is where the attacks sit on the device, top row first, and
    ``attacks`` is what those positions currently mean. A layout is built with
    the Street Fighter six on it; :func:`with_buttons` lays another game's set
    onto the same positions. See :mod:`.buttons`.
    """

    key: str
    name: str
    description: str
    movement: dict[str, Axis]
    attacks: dict[str, Button]
    attack_rows: tuple[tuple[str, ...], ...] = ()
    kind: LayoutKind = LayoutKind.KEYBOARD
    available: bool = True
    key_labels: dict[str, str] = field(default_factory=dict)
    """Friendlier names for binding codes that are not literal keys, e.g.
    ``{"pad:2": "X"}`` so the gamepad help reads ``LP=X`` not ``LP=pad:2``."""

    @property
    def bindings(self) -> dict[str, Axis | Button]:
        """Every binding in one dict, for lookup on a key press."""
        combined: dict[str, Axis | Button] = dict(self.movement)
        combined.update(self.attacks)
        return combined

    def key_label(self, key: str) -> str:
        """What to call a binding code on screen."""
        if key in self.key_labels:
            return self.key_labels[key]
        return friendly_key(key)

    def bound_rows(self) -> tuple[tuple[tuple[str, Button], ...], ...]:
        """The attack positions that currently mean something, row by row.

        This is what the input display draws: the physical panel, with the keys
        that a shorter button set leaves over dropped.
        """
        return tuple(tuple((key, self.attacks[key]) for key in row if key in self.attacks) for row in self.attack_rows)

    def movement_help(self) -> str:
        """Human readable movement bindings, e.g. 'a s d space'."""
        if self.kind is LayoutKind.GAMEPAD:
            return "D-pad / left stick"
        order = (Axis.LEFT, Axis.DOWN, Axis.RIGHT, Axis.UP)
        by_axis = {axis: key for key, axis in self.movement.items()}
        return " ".join(self.key_label(by_axis[axis]) for axis in order if axis in by_axis)

    def attack_help(self) -> str:
        """Human readable attack bindings, e.g. 'LP=u MP=i ...'."""
        # First key wins: a set that binds a button twice, as the Neo Geo does,
        # is named by the row it is written in rather than the duplicate.
        by_button: dict[Button, str] = {}
        for key, button in self.attacks.items():
            by_button.setdefault(button, key)
        return " ".join(
            f"{button.value}={self.key_label(by_button[button])}" for button in Button if button in by_button
        )


def lay_out(rows: tuple[tuple[str, ...], ...], buttons: ButtonSet) -> dict[str, Button]:
    """Lay a button set onto rows of attack keys, position by position.

    A row of the set that is longer than the layout's row runs out of keys, and
    keys past the end of a row are left unbound. A button appearing twice, as
    the Neo Geo's does, simply gets both keys.
    """
    bound: dict[str, Button] = {}
    for keys, row in zip(rows, buttons.rows, strict=False):
        bound.update(zip(keys, row, strict=False))
    return bound


def with_buttons(layout: ControlLayout, buttons: ButtonSet) -> ControlLayout:
    """The same layout with another game's buttons on its attack positions."""
    return replace(layout, attacks=lay_out(layout.attack_rows, buttons))


# The two reference layouts the engine test suite is written against: every
# button of every panel has a key, which is what lets `tests/controls/
# test_buttons.py` and the motion-test harness prove the panel-laying machinery.
# They are not offered in the picker (see `LAYOUTS` below) - the keyboard
# choices a player sees are `KB_LEFT` / `KB_RIGHT` / `KB_CUSTOM`.
HITBOX_ROWS = (("u", "i", "o", "p"), ("j", "k", "l", ";"))
SOUTHPAW_ROWS = (("a", "s", "d", "f"), ("z", "x", "c", "v"))

HITBOX = ControlLayout(
    key="hitbox",
    name="Hitbox",
    description="Left hand on a s d for back/down/forward, space for up. Attacks on u i o p / j k l ;.",
    movement={"a": Axis.LEFT, "s": Axis.DOWN, "d": Axis.RIGHT, "space": Axis.UP},
    attacks=lay_out(HITBOX_ROWS, DEFAULT_SET),
    attack_rows=HITBOX_ROWS,
)

SOUTHPAW = ControlLayout(
    key="southpaw",
    name="Southpaw",
    description="Right hand on j k l for back/down/forward, space for up. Attacks on a s d f / z x c v.",
    movement={"j": Axis.LEFT, "k": Axis.DOWN, "l": Axis.RIGHT, "space": Axis.UP},
    attacks=lay_out(SOUTHPAW_ROWS, DEFAULT_SET),
    attack_rows=SOUTHPAW_ROWS,
)

# The keyboard layouts a player actually picks: the Street Fighter six on three
# keys a hand, one hand on movement and the other on the attacks below it.
KB_LEFT_ROWS = (("j", "k", "l"), ("n", "m", "comma"))
KB_RIGHT_ROWS = (("a", "s", "d"), ("z", "x", "c"))

KB_LEFT = ControlLayout(
    key="keyboard-left",
    name="asd space, jkl nm,",
    description="Left hand a s d space to move. Attacks j k l over n m ,.",
    movement={"a": Axis.LEFT, "s": Axis.DOWN, "d": Axis.RIGHT, "space": Axis.UP},
    attacks=lay_out(KB_LEFT_ROWS, DEFAULT_SET),
    attack_rows=KB_LEFT_ROWS,
)

KB_RIGHT = ControlLayout(
    key="keyboard-right",
    name="jkl space, asd zxc",
    description="Right hand j k l space to move. Attacks a s d over z x c.",
    movement={"j": Axis.LEFT, "k": Axis.DOWN, "l": Axis.RIGHT, "space": Axis.UP},
    attacks=lay_out(KB_RIGHT_ROWS, DEFAULT_SET),
    attack_rows=KB_RIGHT_ROWS,
)

KB_CUSTOM = ControlLayout(
    key="keyboard-custom",
    name="Keyboard (custom)",
    description="Every key rebindable. Highlight this row and press b to set them.",
    movement=dict(KB_LEFT.movement),
    attacks=dict(KB_LEFT.attacks),
    attack_rows=KB_LEFT_ROWS,
)

KEYBOARD_SLOTS: tuple[str, ...] = (
    Axis.LEFT.value,
    Axis.DOWN.value,
    Axis.RIGHT.value,
    Axis.UP.value,
    *(button.name for button in BUTTON_ORDER),
)
"""The rebindable slots of the custom keyboard layout, in the order the rebind
screen lists them: the four movement axes, then the six attacks."""

KEYBOARD_DEFAULT_BINDINGS: dict[str, str] = {
    Axis.LEFT.value: "a",
    Axis.DOWN.value: "s",
    Axis.RIGHT.value: "d",
    Axis.UP.value: "space",
    "LP": "j",
    "MP": "k",
    "HP": "l",
    "LK": "n",
    "MK": "m",
    "HK": "comma",
}
"""What the custom layout starts from: the same keys as ``KB_LEFT``,
``{slot: key name}``."""


def resolve_keyboard_bindings(bindings: Mapping[str, str] | None = None) -> dict[str, str]:
    """A full ``{slot: key name}`` map from a stored, partial one.

    Unknown slots and empty values are ignored; anything left unset keeps its
    default. If two slots end up on one key the default is returned whole, so a
    movement direction or an attack is never left unreachable.
    """
    resolved = dict(KEYBOARD_DEFAULT_BINDINGS)
    resolved.update(
        (slot, key)
        for slot, key in (bindings or {}).items()
        if slot in KEYBOARD_DEFAULT_BINDINGS and isinstance(key, str) and key
    )
    if len(set(resolved.values())) != len(resolved):
        return dict(KEYBOARD_DEFAULT_BINDINGS)
    return resolved


def keyboard_layout(bindings: Mapping[str, str] | None = None) -> ControlLayout:
    """The custom keyboard layout with the player's rebinds applied."""
    resolved = resolve_keyboard_bindings(bindings)
    if resolved == KEYBOARD_DEFAULT_BINDINGS:
        return KB_CUSTOM
    movement = {resolved[axis.value]: axis for axis in (Axis.LEFT, Axis.DOWN, Axis.RIGHT, Axis.UP)}
    rows = (
        (resolved["LP"], resolved["MP"], resolved["HP"]),
        (resolved["LK"], resolved["MK"], resolved["HK"]),
    )
    return replace(KB_CUSTOM, movement=movement, attacks=lay_out(rows, DEFAULT_SET), attack_rows=rows)


def _gamepad_supported() -> bool:
    """Whether the optional ``gamepad`` extra (pygame) is installed."""
    return importlib.util.find_spec("pygame") is not None


# The d-pad and the left stick both feed the movement axes. Attack codes map to
# an Xbox-style pad through SDL's controller database (see controls/gamepad.py),
# so the face names below hold on any recognised pad. `pad:0`-`pad:5` are the
# face and shoulder buttons; `pad:6`/`pad:7` are the triggers. This is the
# default; `gamepad_layout` applies the player's rebinds (`b` on setup) on top.
_PAD_BUTTON_LABELS = {
    "pad:0": "A",
    "pad:1": "B",
    "pad:2": "X",
    "pad:3": "Y",
    "pad:4": "LB",
    "pad:5": "RB",
    "pad:6": "LT",
    "pad:7": "RT",
}

GAMEPAD_ROWS = (("pad:2", "pad:3", "pad:5", "pad:7"), ("pad:0", "pad:1", "pad:4", "pad:6"))
"""X Y RB RT over A B LB LT, so the first three of each row are the Xbox-style
default the six-button rebinding starts from."""

GAMEPAD = ControlLayout(
    key="gamepad",
    name="Gamepad",
    description="D-pad or left stick to move. Press b on this row to rebind the attack buttons.",
    movement={"pad:left": Axis.LEFT, "pad:down": Axis.DOWN, "pad:right": Axis.RIGHT, "pad:up": Axis.UP},
    attacks=lay_out(GAMEPAD_ROWS, DEFAULT_SET),
    attack_rows=GAMEPAD_ROWS,
    kind=LayoutKind.GAMEPAD,
    available=_gamepad_supported(),
    key_labels=_PAD_BUTTON_LABELS,
)

GAMEPAD_DEFAULT_BINDINGS: dict[Button, str] = {button: code for code, button in GAMEPAD.attacks.items()}
"""The attack-button map a fresh install uses: ``{Button: pad code}``."""


PAD_ATTACK_CODES: tuple[str, ...] = tuple(_PAD_BUTTON_LABELS)
"""The pad buttons an attack can be bound to: ``pad:0``..``pad:5`` for the face
and shoulder buttons, ``pad:6``/``pad:7`` for the triggers."""


def resolve_gamepad_bindings(bindings: Mapping[str, str] | None = None) -> dict[Button, str]:
    """A full ``{Button: pad code}`` attack map from a stored, partial one.

    ``bindings`` is the ``{Button name: pad code}`` map as it sits in the
    config. Unknown button names and codes outside :data:`PAD_ATTACK_CODES` are
    ignored; anything left unset keeps its default. If the result is not a
    one-to-one map (a hand-edited config putting two attacks on one button) the
    default is returned whole, so an attack is never left unreachable.
    """
    resolved = dict(GAMEPAD_DEFAULT_BINDINGS)
    for name, code in (bindings or {}).items():
        if name in Button.__members__ and code in _PAD_BUTTON_LABELS:
            resolved[Button[name]] = code
    if len(set(resolved.values())) != len(resolved):
        return dict(GAMEPAD_DEFAULT_BINDINGS)
    return resolved


def gamepad_layout(bindings: Mapping[str, str] | None = None) -> ControlLayout:
    """The gamepad layout with the player's attack-button rebinds applied."""
    resolved = resolve_gamepad_bindings(bindings)
    if resolved == GAMEPAD_DEFAULT_BINDINGS:
        return GAMEPAD
    # Rebuild the rows so each attack keeps its Street Fighter grid position at
    # its rebound code, exactly as `keyboard_layout` does. Without this the
    # input display draws the panel wherever `GAMEPAD_ROWS` happens to place the
    # codes - an attack bound to a trigger jumps into the shoulder row. A spare
    # code trails each row so a wider set (the Neo Geo's four) still lays on
    # through `with_buttons`.
    spare = [code for code in PAD_ATTACK_CODES if code not in resolved.values()]
    rows = (
        (resolved[Button.LP], resolved[Button.MP], resolved[Button.HP], *spare[:1]),
        (resolved[Button.LK], resolved[Button.MK], resolved[Button.HK], *spare[1:2]),
    )
    return replace(GAMEPAD, attacks={code: button for button, code in resolved.items()}, attack_rows=rows)


LAYOUTS: dict[str, ControlLayout] = {layout.key: layout for layout in (KB_LEFT, KB_RIGHT, KB_CUSTOM, GAMEPAD)}
DEFAULT_LAYOUT = KB_LEFT.key


def get_layout(key: str) -> ControlLayout:
    """Look up a layout by key, raising a helpful error for unknown names."""
    try:
        return LAYOUTS[key]
    except KeyError:
        known = ", ".join(LAYOUTS)
        message = f"Unknown layout {key!r}. Known layouts: {known}"
        raise KeyError(message) from None


def available_layouts() -> list[ControlLayout]:
    """Layouts that can actually be used right now."""
    return [layout for layout in LAYOUTS.values() if layout.available]


@dataclass(frozen=True, slots=True)
class HoldTiming:
    """Timings for inferring key holds from presses alone.

    Terminals report key presses and operating system auto-repeats but never
    releases, so a held key has to be deduced:

    * A press marks its axis held for ``tap_ms``. That is long enough for a
      hitbox player to add a second direction and get a diagonal, and short
      enough that the first direction drops away again on its own, which is
      what produces the d, df, f transitions of a quarter circle.
    * Auto-repeat arrives as a burst of presses only milliseconds apart. Once
      ``repeats_to_confirm`` of those have been seen the key is genuinely
      being held, so the window widens to ``hold_ms`` and the hold is
      back-dated to the original press. That is what makes charge moves
      possible.
    * ``bridge_ms`` covers the operating system's initial repeat delay, the
      quiet gap between the first press and the start of the repeat burst.
    * A deliberate double tap of one key has gaps far wider than
      ``repeat_gap_ms``, so it is never mistaken for auto-repeat. This matters:
      it is exactly the input that separates a 3rd Strike dragon punch from a
      fireball.

    None of this applies once the terminal reports real key releases, at which
    point only ``lost_release_ms`` is used, purely as a safety net.
    """

    tap_ms: int = 250
    hold_ms: int = 300
    repeat_gap_ms: int = 80
    repeats_to_confirm: int = 2
    bridge_ms: int = 1200
    adapt: bool = True
    max_tap_ms: int = 700
    lost_release_ms: int = 5000


DEFAULT_TIMING = HoldTiming()

TAP_MARGIN_MS = 60
"""Headroom added to the measured repeat delay when adapting ``tap_ms``."""

MIN_REPEAT_DELAY_MS = 120
"""No keyboard repeats faster than this, so shorter gaps are not repeat delays."""

COMFORTABLE_REPEAT_DELAY_MS = 300
"""Above this, holds are noticeably late to register and motions feel sluggish."""


def repeat_delay_advice(observed_ms: int) -> str:
    """Advice for a keyboard whose repeat delay is slowing the trainer down.

    Held directions can only be detected through auto-repeat, so a long initial
    repeat delay directly widens every motion window. Empty when nothing is
    wrong, or when no repeat has been observed yet.
    """
    if observed_ms <= COMFORTABLE_REPEAT_DELAY_MS:
        return ""
    return (
        f"Key repeat delay is about {observed_ms}ms, which makes held directions slow to register. "
        "Lower it for tighter timing: macOS `defaults write -g InitialKeyRepeat -int 15` (log out and back in), "
        "X11 `xset r rate 200 40`, or your compositor's repeat-delay setting on Wayland."
    )


@dataclass(slots=True)
class AxisHold:
    """One movement axis being held down."""

    first_ms: int
    last_ms: int
    fast_repeats: int = 0
    confirmed: bool = False
    pending_delay_ms: int = 0
    """Gap back to a hold that just lapsed. Only believed as the keyboard's
    repeat delay once this hold turns out to be a genuine auto-repeat burst."""


@dataclass(slots=True)
class HeldAxes:
    """Tracks which movement axes are down, inferring holds from auto-repeat.

    ``tap_ms`` should sit just above the operating system's initial key-repeat
    delay, so that a genuinely held key keeps repeating before its window
    lapses. That delay is a user setting, so it is measured as the player types
    and the window is widened to match. Until then, holding a direction can
    briefly read as a tap.

    All of that is guesswork, and it is switched off the moment a real key
    release arrives. Terminals speaking the kitty keyboard protocol report
    releases, and from the first one onwards this tracks holds exactly.
    """

    timing: HoldTiming = DEFAULT_TIMING
    holds: dict[Axis, AxisHold] = field(default_factory=dict)
    tap_ms: int = 0
    observed_repeat_delay_ms: int = 0
    exact: bool = False
    """True once the terminal has reported a key release, so holds are known
    rather than inferred."""
    _expired: dict[Axis, AxisHold] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Start from the configured tap window."""
        self.tap_ms = self.tap_ms or self.timing.tap_ms

    def note_release_support(self) -> None:
        """Record that the terminal reports key releases.

        One release anywhere proves it, so hold inference can be switched off
        even if the released key was not a movement key.
        """
        self.exact = True

    def release(self, axis: Axis, at_ms: int) -> bool:
        """Handle a real key release. Returns True if the axis was held."""
        del at_ms  # A release is exact; there is no timing to learn from it.
        self.note_release_support()
        self._expired.pop(axis, None)
        return self.holds.pop(axis, None) is not None

    def press(self, axis: Axis, at_ms: int) -> None:
        """Register a press or auto-repeat of a movement key."""
        hold = self.holds.get(axis)
        if hold is not None and at_ms - hold.last_ms <= self._window(hold):
            self._refresh(hold, at_ms)
            return

        pending = 0
        ghost = self._expired.pop(axis, None)
        if ghost is not None and at_ms - ghost.last_ms <= self.timing.bridge_ms:
            pending = at_ms - ghost.first_ms
        self.holds[axis] = AxisHold(first_ms=at_ms, last_ms=at_ms, pending_delay_ms=pending)

    def _observe_repeat_delay(self, delay_ms: int) -> None:
        """Learn the keyboard's initial repeat delay and widen ``tap_ms``.

        Called only once a hold has been proved genuine by a burst of fast
        auto-repeats, so the gap that preceded the burst really was the
        operating system's initial repeat delay rather than the player tapping
        the same key twice.
        """
        if delay_ms < MIN_REPEAT_DELAY_MS or delay_ms <= self.tap_ms:
            return
        self.observed_repeat_delay_ms = max(self.observed_repeat_delay_ms, delay_ms)
        if self.timing.adapt:
            self.tap_ms = min(delay_ms + TAP_MARGIN_MS, self.timing.max_tap_ms)

    def _refresh(self, hold: AxisHold, at_ms: int) -> None:
        gap = at_ms - hold.last_ms
        hold.last_ms = at_ms
        if gap > self.timing.repeat_gap_ms:
            hold.fast_repeats = 0
            return
        hold.fast_repeats += 1
        if hold.fast_repeats >= self.timing.repeats_to_confirm and not hold.confirmed:
            # A burst of presses milliseconds apart is auto-repeat, not typing,
            # so widen the window and stop treating this as a tap.
            hold.confirmed = True
            if hold.pending_delay_ms:
                self._observe_repeat_delay(hold.pending_delay_ms)

    def expire(self, at_ms: int) -> bool:
        """Drop axes that have stopped repeating. Returns True if any changed.

        Once releases are being reported this only acts as a safety net, in
        case one is lost while the terminal is not focused.
        """
        stale = [axis for axis, hold in self.holds.items() if at_ms - hold.last_ms > self._window(hold)]
        for axis in stale:
            self._expired[axis] = self.holds.pop(axis)
        for axis, ghost in list(self._expired.items()):
            if at_ms - ghost.last_ms > self.timing.bridge_ms:
                del self._expired[axis]
        return bool(stale)

    def held(self) -> frozenset[Axis]:
        """The axes currently considered held."""
        return frozenset(self.holds)

    def newer_horizontal(self) -> str:
        """Which of left/right was pressed most recently, for SOCD cleaning."""
        left, right = self.holds.get(Axis.LEFT), self.holds.get(Axis.RIGHT)
        if left is None or right is None:
            return ""
        return "left" if left.first_ms > right.first_ms else "right"

    def clear(self) -> None:
        """Release everything."""
        self.holds.clear()
        self._expired.clear()

    def _window(self, hold: AxisHold) -> int:
        if self.exact:
            return self.timing.lost_release_ms
        return self.timing.hold_ms if hold.confirmed else self.tap_ms
