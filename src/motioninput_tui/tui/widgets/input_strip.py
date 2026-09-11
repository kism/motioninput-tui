"""The rolling display of what the player actually pressed."""

from typing import TYPE_CHECKING, NamedTuple

from rich.cells import cell_len
from rich.text import Text
from textual.widgets import Static

from motioninput_tui.engine.notation import Direction

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from motioninput_tui.engine.session import InputEntry

CATEGORY_STYLES: dict[str, str] = {
    "super": "bold magenta",
    "special": "bold green",
    "command": "cyan",
    "throw": "yellow",
    "movement": "blue",
    "other": "white",
}


class Bracket(NamedTuple):
    """A label laid over the run of inputs made between two moments."""

    label: str
    style: str
    start_ms: int
    end_ms: int


def _bracket(bracket: Bracket, columns: Sequence[tuple[int, int, int]]) -> Text:
    """The label over the inputs it covers, ruled out to their width.

    ``columns`` is each input's moment, and the columns it starts and ends at.
    """
    inside = [(start, end) for at_ms, start, end in columns if bracket.start_ms <= at_ms <= bracket.end_ms]
    line = Text()
    if not inside:
        return line
    left, right = inside[0][0], inside[-1][1]
    rule = right - left - cell_len(bracket.label) - 1
    line.append(" " * left)
    line.append(f"{bracket.label} {'─' * rule}" if rule > 0 else bracket.label, style=bracket.style)
    return line


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

    def show(self, entries: Iterable[InputEntry], current: Direction, brackets: Sequence[Bracket] = ()) -> None:
        """Redraw the strip, with ``brackets`` drawn over it, top line first."""
        text = Text()
        columns: list[tuple[int, int, int]] = []
        for entry in entries:
            if text:
                text.append("  ")
            start = len(text)
            style = "bold white" if entry.direction is not Direction.NEUTRAL else "dim"
            if entry.activated:
                style = "bold green"
            text.append(entry.direction.glyph, style=style)
            if entry.buttons:
                labels = "+".join(button.value for button in entry.buttons)
                text.append(labels, style="bold yellow" if not entry.activated else "bold green")
            columns.append((entry.at_ms, start, len(text)))

        text.append("   ")
        text.append(f"[{current.short}]", style="dim")
        # Keep the newest input visible when the history is wider than the pane.
        width = max(self.size.width - 2, 10)
        trim = max(len(text) - width, 0)
        text = text[trim:]
        columns = [(at_ms, max(start - trim, 0), end - trim) for at_ms, start, end in columns if end > trim]
        lines = [_bracket(bracket, columns) for bracket in brackets]
        self.update(Text("\n", no_wrap=True, overflow="ignore").join([*lines, text]))
