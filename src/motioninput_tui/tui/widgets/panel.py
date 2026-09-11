"""The panel, drawn: a direction gate and a row of buttons, lit as you press.

Both are boxes on a grid, so they share one drawing routine. What is held is
filled in rather than merely coloured, which is the difference you can see out
of the corner of your eye while your hands are busy.
"""

from typing import TYPE_CHECKING

from rich.cells import cell_len
from rich.text import Text
from textual.widgets import Static

from motioninput_tui.engine.notation import Direction

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from motioninput_tui.controls.layouts import ControlLayout
    from motioninput_tui.engine.notation import Button
    from motioninput_tui.notation_styles import Notation

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

    def show(self, direction: Direction, notation: Notation) -> None:
        """Light the cell being held, every cell labelled in the player's direction style.

        A style with labels wider than one cell, as letters are, leans each the
        way its cell points, the left column's to the left and the right
        column's to the right, so the two letters of ``DF`` sit in a box three
        wide without reading as the middle one's. One-wide labels stay centred.
        """
        labels = [[notation.directions((cell,)) for cell in row] for row in GATE]
        lean = any(cell_len(label) > 1 for row in labels for label in row)
        rows = (
            boxes(
                [
                    ((_lean(label, column) if lean else label,), cell is direction)
                    for column, (cell, label) in enumerate(zip(row, row_labels, strict=True))
                ],
                DIRECTION_WIDTH,
            )
            for row, row_labels in zip(GATE, labels, strict=True)
        )
        self.art = _stack(rows)
        self.update(self.art)


def _lean(label: str, column: int) -> str:
    """``label`` pushed to the side of its box that the column points at; the middle one stays centred."""
    if column == 0:
        return label.ljust(DIRECTION_WIDTH)
    if column == len(GATE[0]) - 1:
        return label.rjust(DIRECTION_WIDTH)
    return label


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
