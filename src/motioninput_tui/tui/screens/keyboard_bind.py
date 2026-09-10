"""Modal for rebinding the custom keyboard layout.

Opened with ``b`` from the layout picker when the "Keyboard (custom)" row is
selected. Unlike the gamepad, movement is rebindable here too: the four axes and
the six attacks are all in the list. Arm a row, press the key you want, done.
The result is a ``{slot: key name}`` map, or ``None`` if nothing changed.
"""

from typing import TYPE_CHECKING, ClassVar, override

from rich.text import Text
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, Label, OptionList

from motioninput_tui.controls.layouts import (
    KEYBOARD_DEFAULT_BINDINGS,
    KEYBOARD_SLOTS,
    friendly_key,
    resolve_keyboard_bindings,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from textual.app import ComposeResult


_SLOT_LABELS = {"left": "back", "down": "down", "right": "forward", "up": "up"}
"""The movement axes read as fighting-game directions in the list."""


class KeyboardBindScreen(ModalScreen["dict[str, str] | None"]):
    """Pick a slot, press a key, done."""

    BINDINGS: ClassVar = [
        # An armed row takes space as a key: on_key sees it before this does.
        Binding("space", "arm", "Rebind"),
        Binding("escape", "close", "Done"),
        Binding("enter", "close", "Done", priority=True, show=False),
        Binding("r", "reset", "Defaults"),
        # Nothing here takes text input, so drop Screen's copy/paste bindings
        # from the key panel; ctrl+c stays as the quit shortcut.
        Binding("ctrl+c", "app.help_quit", show=False, system=True),
    ]

    DEFAULT_CSS = """
    KeyboardBindScreen { align: center middle; }
    KeyboardBindScreen > Vertical {
        width: 46; height: auto; padding: 1 2;
        background: $surface; border: thick $primary;
    }
    KeyboardBindScreen Label { width: 100%; text-align: center; }
    KeyboardBindScreen #hint { color: $text-muted; margin-bottom: 1; }
    KeyboardBindScreen OptionList { height: 11; border: none; background: $surface; }
    """

    def __init__(self, bindings: Mapping[str, str]) -> None:
        """Start from the current map."""
        super().__init__()
        self._original: dict[str, str] = resolve_keyboard_bindings(bindings)
        self._keys: dict[str, str] = dict(self._original)
        self._armed: str | None = None
        """The slot waiting to take the next key press, if any."""

    @override
    def compose(self) -> ComposeResult:
        """The ten slots in a list, with a status line above."""
        with Vertical():
            yield Label("Rebind keyboard", id="title")
            yield Label(id="hint")
            yield OptionList(id="binds")
        yield Footer()

    def on_mount(self) -> None:
        """Fill the list."""
        self._render_rows()
        self.query_one("#binds", OptionList).focus()
        self._update_hint()

    def _render_rows(self) -> None:
        binds = self.query_one("#binds", OptionList)
        keep = binds.highlighted
        binds.clear_options()
        for slot in KEYBOARD_SLOTS:
            label = _SLOT_LABELS.get(slot, slot)
            face = "press a key…" if slot == self._armed else friendly_key(self._keys[slot])
            binds.add_options([f"{label:<8} →  {face}"])
        binds.highlighted = keep if keep is not None else 0

    def _current(self) -> str | None:
        index = self.query_one("#binds", OptionList).highlighted
        return KEYBOARD_SLOTS[index] if index is not None else None

    def _update_hint(self) -> None:
        if self._armed is not None:
            text = Text(f"Press a key for {_SLOT_LABELS.get(self._armed, self._armed)}…", style="cyan")
        else:
            text = Text("space to rebind · enter when done")
        self.query_one("#hint", Label).update(text)

    def on_option_list_option_selected(self, _event: OptionList.OptionSelected) -> None:
        """A click arms a row, the same as space."""
        self.action_arm()

    def action_arm(self) -> None:
        """Space: arm the highlighted row (or disarm it) for the next key."""
        target = self._current()
        self._armed = None if target == self._armed else target
        self._render_rows()
        self._update_hint()

    def on_option_list_option_highlighted(self, _event: OptionList.OptionHighlighted) -> None:
        """Moving to a different row drops a pending capture."""
        if self._armed is not None and self._current() != self._armed:
            self._armed = None
            self._render_rows()
            self._update_hint()

    def on_key(self, event) -> None:  # ruff: ignore[missing-type-function-argument] - textual.events.Key
        """While a row is armed, the next real key press binds it."""
        if self._armed is None:
            return
        char = event.character
        typed = char is not None and len(char) == 1 and char.isprintable() and not char.isspace()
        if not typed and event.key != "space":
            return
        event.stop()
        event.prevent_default()
        self._assign(self._armed, event.key)

    def action_reset(self) -> None:
        """Back to the built-in map."""
        self._keys = dict(KEYBOARD_DEFAULT_BINDINGS)
        self._armed = None
        self._render_rows()
        self._update_hint()

    def action_close(self) -> None:
        """Leave, handing back the new map only if something actually moved."""
        if self._armed is not None:
            self._armed = None
            self._render_rows()
            self._update_hint()
            return
        if self._keys == self._original:
            self.dismiss(None)
            return
        self.dismiss(dict(self._keys))

    def _assign(self, slot: str, key: str) -> None:
        """Give ``slot`` the key ``key``, swapping whichever slot had it."""
        for other, other_key in self._keys.items():
            if other_key == key and other != slot:
                self._keys[other] = self._keys[slot]
                break
        self._keys[slot] = key
        self._armed = None
        self._render_rows()
        self._update_hint()
