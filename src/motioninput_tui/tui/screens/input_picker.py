"""First screen: what are you playing on?

The input device is picked on its own, before anything else, because it decides
how the trainer reads you rather than what you are training. Choosing it here
also keeps the gamepad rebinding (``b``) and the pad detection polling out of
the setup screen, which is then only about what to train.
"""

from typing import TYPE_CHECKING, ClassVar

from rich.text import Text
from textual.binding import Binding
from textual.containers import Vertical
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, OptionList, Static

from motioninput_tui.controls.layouts import LayoutKind, available_layouts, gamepad_layout
from motioninput_tui.terminal import detect

from .gamepad_bind import GamepadBindScreen

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from motioninput_tui.controls.gamepad import GamepadReader
    from motioninput_tui.controls.layouts import ControlLayout


class InputPickerScreen(Screen[str]):
    """Pick a control layout. Dismisses with its key.

    There is nothing behind this screen to go back to, so it has no escape
    binding; ctrl+q and ctrl+c leave the program as they do everywhere else.
    """

    BINDINGS: ClassVar = [
        Binding("enter", "choose", "Continue", priority=True),
        Binding("b", "bind_gamepad", "Rebind pad"),
        Binding("ctrl+q", "quit", "Quit"),
        # Nothing here takes text input, so drop Screen's copy/paste bindings
        # from the key panel; ctrl+c stays as the quit shortcut.
        Binding("ctrl+c", "app.help_quit", show=False, system=True),
    ]

    class GamepadBindingsChanged(Message):
        """Posted when the player rebinds the pad, so the app can save it."""

        def __init__(self, bindings: dict[str, str]) -> None:
            """Carry the new ``{button name: pad code}`` map."""
            super().__init__()
            self.bindings = bindings

    DEFAULT_CSS = """
    InputPickerScreen { layout: vertical; }
    InputPickerScreen #warning { padding: 0 2; color: $warning; height: auto; }
    InputPickerScreen #blurb { padding: 1 2 0 2; height: auto; }
    InputPickerScreen #choices { height: 1fr; padding: 1 2; }
    InputPickerScreen #choices Label { text-style: bold; }
    InputPickerScreen #layouts { height: 1fr; border: solid $panel; }
    InputPickerScreen #detail { height: 4; padding: 0 2; color: $text-muted; }
    """

    def __init__(self, layout_key: str | None = None, *, gamepad_bindings: dict[str, str] | None = None) -> None:
        """Open on ``layout_key``, with ``gamepad_bindings`` on the pad entry."""
        super().__init__()
        self._gamepad_bindings = dict(gamepad_bindings or {})
        self.layouts = self._build_layouts()
        self.terminal = detect()
        self._initial = layout_key
        self._reader: GamepadReader | None = None
        self._pad_name: str | None = None

    def _build_layouts(self) -> list[ControlLayout]:
        """Available layouts, with the player's rebinds on the gamepad entry."""
        return [
            gamepad_layout(self._gamepad_bindings) if layout.kind is LayoutKind.GAMEPAD else layout
            for layout in available_layouts()
        ]

    def _gamepad_index(self) -> int | None:
        """Row of the gamepad layout in the picker, or None if it is unavailable."""
        for index, layout in enumerate(self.layouts):
            if layout.kind is LayoutKind.GAMEPAD:
                return index
        return None

    def compose(self) -> ComposeResult:
        """One list, filling the screen, with the bindings underneath it."""
        yield Header()
        yield Static(
            Text.from_markup("Motion input trainer. Pick what you are playing on, then press [b]enter[/b]."),
            id="blurb",
        )
        if self.terminal.should_warn:
            yield Static(Text(f"⚠ {self.terminal.warning()}"), id="warning")
        with Vertical(id="choices"):
            yield Label("Input")
            yield OptionList(*[layout.name for layout in self.layouts], id="layouts")
        yield Static(id="detail")
        yield Footer()

    def on_mount(self) -> None:
        """Open on the remembered layout and start watching for a pad."""
        self.title = "motioninput-tui"
        self.sub_title = f"{self.terminal.name} ({self.terminal.speed})"
        # An OptionList highlights its first entry when options are added and
        # posts an event for it, so the remembered one has to wait until those
        # have been dealt with or it gets overwritten.
        self.call_after_refresh(self._apply_initial)
        if self._gamepad_index() is not None:
            self.set_interval(0.25, self._poll_pad)

    def _apply_initial(self) -> None:
        """Open on whatever was used last time."""
        layouts = self.query_one("#layouts", OptionList)
        keys = [layout.key for layout in self.layouts]
        layouts.highlighted = keys.index(self._initial) if self._initial in keys else 0
        layouts.focus()

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        """Describe the highlighted layout, and wake the pad reader for it."""
        if event.option_index == self._gamepad_index():
            self._ensure_reader()
        self.refresh_bindings()
        self._describe()

    def on_option_list_option_selected(self, _event: OptionList.OptionSelected) -> None:
        """Clicking a layout takes it, the same as enter does."""
        self.action_choose()

    def _ensure_reader(self) -> None:
        """Open a gamepad reader the first time the gamepad row is looked at.

        pygame is a heavy import, so it is put off until someone actually
        highlights the gamepad layout rather than paid on every launch.
        """
        if self._reader is not None:
            return
        from motioninput_tui.controls.gamepad import (  # ruff: ignore[import-outside-top-level] - optional dependency, gamepad row only
            GamepadReader,
        )

        self._reader = GamepadReader()

    def _poll_pad(self) -> None:
        """Track the connected pad's name and show it on the gamepad row."""
        reader = self._reader
        # A pushed modal (the rebind screen) polls the same reader; stay out of
        # its way so it, not this, sees the button presses.
        if reader is None or self.app.screen is not self:
            return
        reader.poll(0)
        name = reader.name if reader.connected else None
        if name == self._pad_name:
            return
        self._pad_name = name
        index = self._gamepad_index()
        if index is not None:
            self.query_one("#layouts", OptionList).replace_option_prompt_at_index(index, name or "Gamepad")
            self._describe()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        """Only offer the rebind hotkey while the gamepad row is highlighted."""
        del parameters
        if action != "bind_gamepad":
            return True
        return True if self._highlighted_index() == self._gamepad_index() else None

    def action_bind_gamepad(self) -> None:
        """Open the attack-button rebind modal for the gamepad layout."""
        self._ensure_reader()
        self.app.push_screen(GamepadBindScreen(self._gamepad_bindings, self._reader), self._on_rebind)

    def _on_rebind(self, bindings: dict[str, str] | None) -> None:
        """Apply and remember a map that came back from the rebind modal."""
        if bindings is None:
            return
        self._gamepad_bindings = bindings
        self.layouts = self._build_layouts()
        self._describe()
        self.post_message(self.GamepadBindingsChanged(bindings))

    def _highlighted_index(self) -> int:
        return self.query_one("#layouts", OptionList).highlighted or 0

    def _describe(self) -> None:
        layout = self.layouts[self._highlighted_index()]
        text = Text()
        text.append(f"{layout.description}\n", style="bold")
        text.append(f"Move: {layout.movement_help()}    Attack: {layout.attack_help()}")
        self.query_one("#detail", Static).update(text)

    def action_choose(self) -> None:
        """Hand the chosen layout back to the app."""
        self.dismiss(self.layouts[self._highlighted_index()].key)
