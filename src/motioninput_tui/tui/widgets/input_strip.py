"""The rolling display of what the player actually pressed."""

from typing import TYPE_CHECKING

from rich.text import Text
from textual.widgets import Static

from motioninput_tui.engine.notation import Direction

if TYPE_CHECKING:
    from collections.abc import Iterable

    from motioninput_tui.engine.session import InputEntry

CATEGORY_STYLES: dict[str, str] = {
    "super": "bold magenta",
    "special": "bold green",
    "command": "cyan",
    "throw": "yellow",
    "movement": "blue",
    "other": "white",
}


class InputStrip(Static):
    """Shows recent inputs oldest to newest, left to right."""

    DEFAULT_CSS = """
    InputStrip {
        height: 3;
        padding: 1 1 0 1;
        border-bottom: solid $panel;
        content-align: left middle;
    }
    """

    def show(self, entries: Iterable[InputEntry], current: Direction) -> None:
        """Redraw the strip."""
        text = Text(no_wrap=True, overflow="ignore")
        for entry in entries:
            if text:
                text.append("  ")
            style = "bold white" if entry.direction is not Direction.NEUTRAL else "dim"
            if entry.activated:
                style = "bold green"
            text.append(entry.direction.glyph, style=style)
            if entry.buttons:
                labels = "+".join(button.value for button in entry.buttons)
                text.append(labels, style="bold yellow" if not entry.activated else "bold green")

        text.append("   ")
        text.append(f"[{current.short}]", style="dim")
        # Keep the newest input visible when the history is wider than the pane.
        width = max(self.size.width - 2, 10)
        if len(text) > width:
            text = text[len(text) - width :]
        self.update(text)
