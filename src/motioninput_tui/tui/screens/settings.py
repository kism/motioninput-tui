"""The settings as a modal, for changing them without leaving a session.

The same settings as the setup screen's pane, on the same widget, so the buffer
rule and the half circle rule are in one place rather than one being a hotkey
and the other a screen. The app applies whatever comes back to the session
already running.
"""

from typing import TYPE_CHECKING, ClassVar, override

from rich.text import Text
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, Label

from motioninput_tui.tui.widgets.settings_list import SettingsList

if TYPE_CHECKING:
    from collections.abc import Mapping

    from textual.app import ComposeResult
    from textual.widgets import OptionList


class SettingsScreen(ModalScreen[None]):
    """Toggle settings over whatever is underneath, then escape out."""

    BINDINGS: ClassVar = [
        Binding("escape,ctrl+b", "close", "Done"),
        # Space flips a setting, so enter has nothing else to mean here.
        Binding("enter", "close", "Done", priority=True, show=False),
        # Nothing here takes text input, so drop Screen's copy/paste bindings
        # from the key panel; ctrl+c stays as the quit shortcut.
        Binding("ctrl+c,super+c", "app.help_quit", show=False, system=True),
    ]

    DEFAULT_CSS = """
    SettingsScreen { align: center middle; }
    SettingsScreen > Vertical {
        width: 72; height: auto; padding: 1 2;
        background: $surface; border: thick $primary;
    }
    SettingsScreen #title { width: 100%; text-align: center; text-style: bold; }
    SettingsScreen #detail { width: 100%; height: 4; color: $text-muted; }
    SettingsScreen SettingsList { height: auto; border: none; background: $surface; }
    """

    def __init__(self, values: Mapping[str, bool]) -> None:
        """Open on every setting's current value, keyed by config attribute."""
        super().__init__()
        self._values = dict(values)

    @override
    def compose(self) -> ComposeResult:
        """The toggles, with the highlighted one explained under them."""
        with Vertical():
            yield Label("Settings", id="title")
            yield SettingsList(self._values)
            yield Label(id="detail")
        yield Footer()

    def on_mount(self) -> None:
        """Start on the list, since it is the only thing here."""
        self.query_one(SettingsList).focus()
        self._describe()

    def on_option_list_option_highlighted(self, _event: OptionList.OptionHighlighted) -> None:
        """Explain whatever the cursor moved to."""
        self._describe()

    def on_settings_list_changed(self, _event: SettingsList.Changed) -> None:
        """Keep the description in step. The app saves it as this bubbles past."""
        self._describe()

    def _describe(self) -> None:
        pane = self.query_one(SettingsList)
        setting = pane.highlighted_setting
        text = Text()
        if setting is not None:
            state = "on" if pane.is_on(setting) else "off"
            text.append(f"{setting.name}: {state}\n", style="bold")
            text.append(setting.detail)
        self.query_one("#detail", Label).update(text)

    def action_close(self) -> None:
        """Leave; every toggle has already been applied and saved."""
        self.dismiss(None)
