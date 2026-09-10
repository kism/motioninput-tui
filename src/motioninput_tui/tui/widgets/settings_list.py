"""The global settings as a list of toggles.

Shared by the setup screen's settings pane and the trainer's settings modal, so
a setting looks the same and flips the same way wherever it is met. A change is
posted as :class:`SettingsList.Changed` and bubbles to the app, which owns the
config and decides what the change means for whatever is running.
"""

from typing import TYPE_CHECKING, ClassVar

from rich.text import Text
from textual.binding import Binding
from textual.message import Message
from textual.widgets import OptionList

from motioninput_tui.settings import SETTINGS

if TYPE_CHECKING:
    from collections.abc import Mapping

    from motioninput_tui.settings import Setting


class SettingsList(OptionList):
    """One row per setting; space or a click flips it rather than choosing it.

    Enter is left to whatever screen this sits on, which is why every host
    binds it with priority: on the setup screen it starts training, and in the
    settings modal it closes.
    """

    BINDINGS: ClassVar = [Binding("space", "toggle_setting", "Toggle")]

    class Changed(Message):
        """Posted when a setting is toggled, with every setting's value."""

        def __init__(self, values: dict[str, bool]) -> None:
            """Carry the values keyed by config attribute, as the app writes them."""
            super().__init__()
            self.values = values

    def __init__(self, values: Mapping[str, bool]) -> None:
        """Start from every setting's current value, keyed by config attribute."""
        super().__init__()
        self._values = dict(values)

    def on_mount(self) -> None:
        """Draw the rows once there is a widget to draw them in."""
        self._render_rows()

    @property
    def highlighted_setting(self) -> Setting | None:
        """The setting the cursor is on, for whoever wants to describe it."""
        index = self.highlighted
        return SETTINGS[index] if index is not None and index < len(SETTINGS) else None

    def is_on(self, setting: Setting) -> bool:
        """Whether ``setting`` is currently on."""
        return self._values[setting.attribute]

    def action_toggle_setting(self) -> None:
        """Space: flip the highlighted row.

        Not ``action_toggle``: Textual already has one of those, for flipping a
        reactive attribute by name.
        """
        self.toggle()

    def toggle(self, index: int | None = None) -> None:
        """Flip a row, the highlighted one by default."""
        target = self.highlighted if index is None else index
        if target is None or target >= len(SETTINGS):
            return
        setting = SETTINGS[target]
        self._values[setting.attribute] = not self._values[setting.attribute]
        self._render_rows()
        self.post_message(self.Changed(dict(self._values)))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """A click flips the row it landed on: a setting is never chosen.

        Stopping it also keeps the click from being counted twice by a screen
        that treats a selection on its other lists as a choice.
        """
        event.stop()
        self.toggle(event.option_index)

    def _render_rows(self) -> None:
        """Redraw every row, keeping the cursor where it was."""
        keep = self.highlighted
        self.clear_options()
        self.add_options([self._prompt(setting) for setting in SETTINGS])
        self.highlighted = keep if keep is not None else 0

    def _prompt(self, setting: Setting) -> Text:
        # The box says whether it is on; colouring it as well only competes
        # with the cursor for the eye.
        mark = "[✓] " if self._values[setting.attribute] else "[ ] "
        return Text(mark + setting.name)
