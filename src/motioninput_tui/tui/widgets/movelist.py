"""The reference move list for the selected character."""

from typing import TYPE_CHECKING, override

from rich.cells import cell_len
from rich.text import Text
from textual.containers import VerticalScroll
from textual.widgets import Static

from motioninput_tui.games.models import Category

from .input_strip import CATEGORY_STYLES
from .panel import LIT

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from motioninput_tui.engine.recognizer import RecognisableMove
    from motioninput_tui.games.models import Character, Move
    from motioninput_tui.notation_styles import Notation

_ORDER = (Category.SUPER, Category.SPECIAL, Category.COMMAND, Category.THROW, Category.MOVEMENT, Category.OTHER)

NAME_WIDTH = 23
COMMAND_WIDTH = 21
SUPER_ART_WIDTH = 5
"""Room for ``III`` plus the marker on the equipped one, and a trailing space."""

LIT_ROW = f"{LIT} not dim not strike"
"""The row of the move that just came out, lit like a held button on the panel."""


def _fit(command: str) -> str:
    """Trim a written command down to something that fits the panel."""
    if len(command) > COMMAND_WIDTH:
        return command[: COMMAND_WIDTH - 1] + "…"
    return command


def _pad(text: str, width: int) -> str:
    """Pad to ``width`` terminal cells, which ``len`` miscounts for kanji."""
    return text + " " * (width - cell_len(text))


def _super_art_marker(super_art: str, *, equipped: bool) -> str:
    """The gutter each row starts in: blank, or the Super Art it belongs to."""
    if not super_art:
        return " " * SUPER_ART_WIDTH
    return f"{'▸' if equipped else ' '}{super_art:<3} "


def _row_style(move: Move, *, equipped: bool, full: bool) -> str:
    """Struck through if untrainable (but never full screen), dim if its Super Art is not equipped."""
    if not move.trainable and not full:
        return "dim strike"
    if not equipped:
        return "dim"
    return CATEGORY_STYLES.get(move.category, "white")


class MoveList(VerticalScroll):
    """Every move for a character, grouped, with untrainable ones dimmed."""

    DEFAULT_CSS = """
    MoveList {
        width: 52;
        border-left: solid $panel;
        padding: 0 1;
        scrollbar-size-vertical: 1;
    }
    """

    @override
    def compose(self) -> ComposeResult:
        """Hold a single Static that we repaint wholesale."""
        yield Static(id="movelist-body")

    def show(
        self,
        character: Character,
        notation: Notation,
        super_art: str = "",
        *,
        full: bool = False,
        lit: RecognisableMove | None = None,
    ) -> None:
        """Render this character's move list, written in ``notation``.

        ``super_art`` is the equipped one: the others stay listed for reference
        but are dimmed, since they cannot come out. ``lit`` is the move that
        just did, whose row is lit.

        ``full`` is the whole-screen view: nothing struck through, columns as
        wide as their longest entry, and the guide's own wording beside the
        rewritten input wherever the two differ.
        """
        rows = [(move, notation.write_move(move)) for move in character.moves]
        by_category: dict[str, list[tuple[Move, str]]] = {}
        for move, written in rows:
            by_category.setdefault(move.category, []).append((move, written))
        name_width = max((cell_len(move.name) for move, _ in rows), default=0) + 2
        command_width = max((cell_len(written) for move, written in rows if written != move.command), default=0) + 2

        text = Text(no_wrap=True, overflow="ellipsis")
        if full:
            header = f"{' ' * SUPER_ART_WIDTH}{_pad('Move', name_width)}{_pad('Input', command_width)}Guide\n\n"
            text.append(header, style="dim")
        for category in _ORDER:
            moves = by_category.get(category)
            if not moves:
                continue
            text.append(f"{category.upper()}\n", style="bold underline")
            for move, written in moves:
                equipped = not move.super_art or move.super_art == super_art
                style = _row_style(move, equipped=equipped, full=full)
                start = len(text)
                text.append(_super_art_marker(move.super_art, equipped=equipped), style=style)
                if full:
                    text.append(_pad(move.name, name_width), style=style)
                    text.append(_pad(written, command_width))
                    text.append(move.command if written != move.command else "", style="dim")
                else:
                    text.append(f"{move.name[:NAME_WIDTH]:<{NAME_WIDTH + 1}}", style=style)
                    text.append(_fit(written), style="dim")
                if move is lit:
                    text.stylize(LIT_ROW, start)
                text.append("\n")
            text.append("\n")

        untrainable = sum(1 for move in character.moves if not move.trainable)
        if untrainable and not full:
            text.append(
                f"{untrainable} struck through need context the trainer has no model of\n",
                style="dim italic",
            )
        self.query_one("#movelist-body", Static).update(text)
