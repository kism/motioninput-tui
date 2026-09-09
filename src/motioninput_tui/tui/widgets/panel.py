"""The panel, drawn: a direction gate and a row of buttons, lit as you press.

Both are boxes on a grid, so they share one drawing routine. What is held is
filled in rather than merely coloured, which is the difference you can see out
of the corner of your eye while your hands are busy.
"""

from typing import TYPE_CHECKING

from rich.text import Text
from textual.widgets import Static

from motioninput_tui.engine.notation import Direction

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from motioninput_tui.controls.layouts import ControlLayout
    from motioninput_tui.engine.notation import Button

LIT = "bold black on green"
IDLE = "dim"
GAP = " "

GATE: tuple[tuple[Direction, ...], ...] = (
    (Direction.UP_BACK, Direction.UP, Direction.UP_FORWARD),
    (Direction.BACK, Direction.NEUTRAL, Direction.FORWARD),
    (Direction.DOWN_BACK, Direction.DOWN, Direction.DOWN_FORWARD),
)
"""The eight directions and neutral, in the numpad's own shape."""

DIRECTION_WIDTH = 3
BUTTON_WIDTH = 5


def boxes(cells: Sequence[tuple[Sequence[str], bool]], width: int) -> list[Text]:
    """One row of boxes, as the lines that draw it.

    Each cell is its label lines and whether it is lit. Cells with fewer labels
    than their neighbours are padded, so a row is always square.
    """
    labels = max((len(rows) for rows, _ in cells), default=0)
    lines = [Text() for _ in range(labels + 2)]
    for index, (rows, lit) in enumerate(cells):
        style = LIT if lit else IDLE
        if index:
            for line in lines:
                line.append(GAP)
        lines[0].append(f"╭{'─' * width}╮", style)
        for offset in range(labels):
            label = rows[offset] if offset < len(rows) else ""
            lines[offset + 1].append(f"│{label.center(width)}│", style)
        lines[-1].append(f"╰{'─' * width}╯", style)
    return lines


def _stack(rows: Iterable[list[Text]]) -> Text:
    lines: list[Text] = []
    for row in rows:
        lines.extend(row)
    return Text("\n").join(lines)


class DirectionGate(Static):
    """The stick, as the nine cells of the numpad."""

    DEFAULT_CSS = """
    DirectionGate { width: auto; height: auto; padding: 0 2; }
    """

    art: Text
    """What is currently drawn. Kept so it can be read back, since a widget's
    rendering is otherwise Textual's business rather than ours."""

    def __init__(self) -> None:
        """Start blank; :meth:`show` draws it."""
        super().__init__()
        self.art = Text()

    def show(self, direction: Direction) -> None:
        """Light the cell being held."""
        self.art = _stack(boxes([((cell.glyph,), cell is direction) for cell in row], DIRECTION_WIDTH) for row in GATE)
        self.update(self.art)


class ButtonPads(Static):
    """The attack buttons in their rows, each showing what it is bound to."""

    DEFAULT_CSS = """
    ButtonPads { width: auto; height: auto; padding: 0 2; }
    """

    art: Text
    """What is currently drawn, as on :class:`DirectionGate`."""

    def __init__(self) -> None:
        """Start blank; :meth:`show` draws it."""
        super().__init__()
        self.art = Text()

    def show(self, layout: ControlLayout, held: Iterable[Button]) -> None:
        """Draw the layout's attack positions, lighting the ones held."""
        down = set(held)
        rows = [
            boxes([((button.value, layout.key_label(key)), button in down) for key, button in row], BUTTON_WIDTH)
            for row in layout.bound_rows()
            if row
        ]
        self.art = _stack(rows)
        self.update(self.art)
