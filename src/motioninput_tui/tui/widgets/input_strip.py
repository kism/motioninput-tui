"""The rolling display of what the player actually pressed."""

from operator import itemgetter
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


type _Placed = tuple[int, int, Bracket]
"""A bracket and the columns it takes, left inclusive, right exclusive."""


def _place(bracket: Bracket, columns: Sequence[tuple[int, int, int]]) -> _Placed | None:
    """Where a bracket goes: over the inputs it covers, or wider if its label is.

    ``columns`` is each input's moment, and the columns it starts and ends at.
    A bracket that falls between two inputs, as a button joining the direction
    already held does, goes over the one before. None for a bracket whose
    inputs have scrolled out of the strip.
    """
    inside = [(start, end) for at_ms, start, end in columns if bracket.start_ms <= at_ms <= bracket.end_ms]
    inside = inside or [(start, end) for at_ms, start, end in columns if at_ms <= bracket.start_ms][-1:]
    if not inside:
        return None
    left = inside[0][0]
    return left, max(inside[-1][1], left + cell_len(bracket.label)), bracket


def _draw(row: list[_Placed]) -> Text:
    """One line of brackets, each label ruled out to the width of its inputs."""
    line = Text()
    for left, right, bracket in sorted(row, key=itemgetter(0)):
        line.append(" " * (left - line.cell_len))
        rule = right - left - cell_len(bracket.label) - 1
        line.append(f"{bracket.label} {'─' * rule}" if rule > 0 else bracket.label, style=bracket.style)
    return line


def _pack(placed: Iterable[_Placed], limit: int) -> list[Text]:
    """Brackets in as few lines as they fit without touching, top line first.

    The first given go nearest the inputs; one that finds no room in ``limit``
    lines is left out.
    """
    rows: list[list[_Placed]] = []
    for left, right, bracket in placed:
        for row in rows:
            if all(right < other_left or left > other_right for other_left, other_right, _ in row):
                row.append((left, right, bracket))
                break
        else:
            if len(rows) < limit:
                rows.append([(left, right, bracket)])
    return [_draw(row) for row in reversed(rows)]


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

    def show(
        self,
        entries: Iterable[InputEntry],
        current: Direction,
        brackets: Sequence[Bracket] = (),
        *,
        bracket_rows: int = 1,
    ) -> None:
        """Redraw the strip, with ``brackets`` over it in up to ``bracket_rows`` lines."""
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
        placed = (spot for bracket in brackets if (spot := _place(bracket, columns)) is not None)
        lines = _pack(placed, bracket_rows)
        self.update(Text("\n", no_wrap=True, overflow="ignore").join([*lines, text]))
