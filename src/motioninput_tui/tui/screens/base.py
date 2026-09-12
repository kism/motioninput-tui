"""What the screens share: the keys every one of them takes, and escape first in the footer."""

from typing import TYPE_CHECKING, ClassVar, override

from textual.binding import Binding
from textual.screen import Screen

from motioninput_tui.tui.widgets.panel import LivePanel

if TYPE_CHECKING:
    from textual.binding import ActiveBinding


class AppScreen[ResultT](Screen[ResultT]):
    """Every screen of the trainer. A modal lists it ahead of ``ModalScreen``.

    Textual merges ``BINDINGS`` down the class hierarchy, so a subclass's own
    are added to these rather than replacing them.
    """

    BINDINGS: ClassVar = [
        # Nothing here takes text input, so drop Screen's copy/paste bindings
        # from the key panel; ctrl+c stays as the quit shortcut.
        Binding("ctrl+c", "app.help_quit", show=False, system=True),
    ]

    @property
    @override
    def active_bindings(self) -> dict[str, ActiveBinding]:
        """The keys the footer shows, escape first wherever it was bound.

        Textual lists the focused widget's keys ahead of the screen's, and a key
        a screen rebinds keeps the place Textual gave it, which put space and tab
        ahead of the way out.
        """
        return dict(sorted(super().active_bindings.items(), key=lambda item: item[0] != "escape"))


# ponytail: unparameterized on purpose. App.screen is a Screen[object], and ty
# takes a Screen[None] for a different type altogether, so a check of which
# screen is showing would narrow to Never and leave the code after it unchecked.
class SessionScreen(AppScreen):
    """A screen running a session: the trainer and the input display."""

    BINDINGS: ClassVar = [
        Binding("escape", "back", "Change character"),
        Binding("ctrl+r", "reset", "Reset"),
        Binding("ctrl+k", "toggle_panel", "Live input"),
        Binding("ctrl+b", "app.settings", "Settings"),
    ]

    def action_toggle_panel(self) -> None:
        """Show or hide the stick and the buttons beside the history."""
        self.query_one(LivePanel).toggle()

    def action_back(self) -> None:
        """Return to the setup screen."""
        self.dismiss(None)
