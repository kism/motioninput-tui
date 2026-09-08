"""The reference move list for the selected character."""

from typing import TYPE_CHECKING, override

from rich.text import Text
from textual.containers import VerticalScroll
from textual.widgets import Static

from motioninput_tui.games.models import Category

from .input_strip import CATEGORY_STYLES

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from motioninput_tui.games.models import Character, Move
    from motioninput_tui.notation_styles import Notation

_ORDER = (Category.SUPER, Category.SPECIAL, Category.COMMAND, Category.THROW, Category.MOVEMENT, Category.OTHER)

NAME_WIDTH = 23
COMMAND_WIDTH = 21
SUPER_ART_WIDTH = 5
"""Room for ``III`` plus the marker on the equipped one, and a trailing space."""


def _fit(command: str) -> str:
    """Trim a written command down to something that fits the panel."""
    if len(command) > COMMAND_WIDTH:
        return command[: COMMAND_WIDTH - 1] + "…"
    return command


def _super_art_marker(super_art: str, *, equipped: bool) -> str:
    """The gutter each row starts in: blank, or the Super Art it belongs to."""
    if not super_art:
        return " " * SUPER_ART_WIDTH
    return f"{'▸' if equipped else ' '}{super_art:<3} "


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

    def show(self, character: Character, notation: Notation, super_art: str = "") -> None:
        """Render this character's move list, written in ``notation``.

        ``super_art`` is the equipped one: the others stay listed for reference
        but are dimmed, since they cannot come out.
        """
        text = Text(no_wrap=True, overflow="ellipsis")
        by_category: dict[str, list[Move]] = {}
        for move in character.moves:
            by_category.setdefault(move.category, []).append(move)

        for category in _ORDER:
            moves = by_category.get(category)
            if not moves:
                continue
            text.append(f"{category.upper()}\n", style="bold underline")
            for move in moves:
                equipped = not move.super_art or move.super_art == super_art
                style = CATEGORY_STYLES.get(move.category, "white")
                if not move.trainable:
                    style = "dim strike"
                elif not equipped:
                    style = "dim"
                text.append(_super_art_marker(move.super_art, equipped=equipped), style=style)
                text.append(f"{move.name[:NAME_WIDTH]:<{NAME_WIDTH + 1}}", style=style)
                text.append(f"{_fit(notation.write_move(move))}\n", style="dim")
            text.append("\n")

        untrainable = sum(1 for move in character.moves if not move.trainable)
        if untrainable:
            text.append(
                f"{untrainable} struck through need context the trainer has no model of\n",
                style="dim italic",
            )
        self.query_one("#movelist-body", Static).update(text)
