"""Modal for rebinding the six gamepad attack buttons.

Opened with ``b`` from the layout picker when the gamepad row is selected.
Movement stays on the d-pad and left stick; only the attack buttons move.
The result is a ``{button name: pad code}`` map, or ``None`` if nothing changed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, override

from rich.text import Text
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, Label, OptionList

from motioninput_tui.controls.layouts import (
    GAMEPAD,
    GAMEPAD_DEFAULT_BINDINGS,
    PAD_ATTACK_CODES,
    resolve_gamepad_bindings,
)
from motioninput_tui.engine.notation import BUTTON_ORDER, Button

if TYPE_CHECKING:
    from collections.abc import Mapping

    from textual.app import ComposeResult

    from motioninput_tui.controls.gamepad import GamepadReader


class GamepadBindScreen(ModalScreen["dict[str, str] | None"]):
    """Pick an attack, press a pad button, done."""

    BINDINGS: ClassVar = [
        Binding("escape", "close", "Done"),
        Binding("r", "reset", "Defaults"),
    ]

    DEFAULT_CSS = """
    GamepadBindScreen { align: center middle; }
    GamepadBindScreen > Vertical {
        width: 46; height: auto; padding: 1 2;
        background: $surface; border: thick $primary;
    }
    GamepadBindScreen Label { width: 100%; text-align: center; }
    GamepadBindScreen #hint { color: $text-muted; margin-bottom: 1; }
    GamepadBindScreen OptionList { height: 6; border: none; background: $surface; }
    """

    def __init__(self, bindings: Mapping[str, str], reader: GamepadReader | None) -> None:
        """Start from the current map; poll ``reader`` for the button to bind."""
        super().__init__()
        self._reader = reader
        self._original: dict[Button, str] = resolve_gamepad_bindings(bindings)
        self._codes: dict[Button, str] = dict(self._original)
        self._armed: Button | None = None
        """The attack waiting to take the next pad button, if any."""

    @override
    def compose(self) -> ComposeResult:
        """The six attacks in a list, with a status line above."""
        with Vertical():
            yield Label("Rebind gamepad attacks", id="title")
            yield Label(id="hint")
            yield OptionList(id="binds")
        yield Footer()

    def on_mount(self) -> None:
        """Fill the list and start polling the pad."""
        self._render_rows()
        self.query_one("#binds", OptionList).focus()
        self._update_hint()
        self.set_interval(0.05, self._poll)

    def _render_rows(self) -> None:
        binds = self.query_one("#binds", OptionList)
        keep = binds.highlighted
        binds.clear_options()
        for button in BUTTON_ORDER:
            code = self._codes[button]
            face = "press a button…" if button is self._armed else f"{GAMEPAD.key_labels[code]}  ({code})"
            binds.add_options([f"{button.value:<3} →  {face}"])
        binds.highlighted = keep if keep is not None else 0

    def _current(self) -> Button | None:
        index = self.query_one("#binds", OptionList).highlighted
        return BUTTON_ORDER[index] if index is not None else None

    def _update_hint(self) -> None:
        if self._reader is None or not self._reader.connected:
            text = Text("Connect a pad to rebind", style="yellow")
        elif self._armed is not None:
            text = Text(f"Press a button on the pad for {self._armed.value}…", style="cyan")
        else:
            text = Text("enter to rebind · esc when done")
        self.query_one("#hint", Label).update(text)

    def on_option_list_option_selected(self, _event: OptionList.OptionSelected) -> None:
        """Enter on a row arms it (or disarms it) for the next pad button."""
        if self._reader is None or not self._reader.connected:
            return
        target = self._current()
        self._armed = None if target is self._armed else target
        self._render_rows()
        self._update_hint()

    def on_option_list_option_highlighted(self, _event: OptionList.OptionHighlighted) -> None:
        """Moving to a different row drops a pending capture."""
        if self._armed is not None and self._current() is not self._armed:
            self._armed = None
            self._render_rows()
            self._update_hint()

    def action_reset(self) -> None:
        """Back to the built-in Xbox-style map."""
        self._codes = dict(GAMEPAD_DEFAULT_BINDINGS)
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
        if self._codes == self._original:
            self.dismiss(None)
            return
        self.dismiss({button.value: code for button, code in self._codes.items()})

    def _poll(self) -> None:
        events = self._reader.poll(0) if self._reader is not None else []
        if self._armed is None:
            return
        for code, pressed in events:
            if pressed and code in PAD_ATTACK_CODES:
                self._assign(self._armed, code)
                return

    def _assign(self, button: Button, code: str) -> None:
        """Give ``button`` the pad button ``code``, swapping whoever had it."""
        for other, other_code in self._codes.items():
            if other_code == code and other is not button:
                self._codes[other] = self._codes[button]
                break
        self._codes[button] = code
        self._armed = None
        self._render_rows()
        self._update_hint()
