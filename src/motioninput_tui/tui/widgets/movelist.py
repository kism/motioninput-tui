"""The reference move list for the selected character."""

from typing import TYPE_CHECKING, override

from rich.cells import cell_len
from rich.text import Text
from textual.containers import VerticalScroll
from textual.geometry import Region
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
"""The narrowest the names get beside the trainer, when the screen has no room to spare."""
SUPER_ART_WIDTH = 5
"""Room for ``III`` plus the marker on the equipped one, and a trailing space."""

MIN_WIDTH = 52
"""The narrowest the list gets beside the trainer, however little room there is."""
FRAME = 4
"""What the list adds around its rows: the border on its left, a cell of padding
each side, and the scrollbar."""

LIT_ROW = f"{LIT} not dim not strike"
"""The row of the move that just came out, lit like a held button on the panel."""

CURSOR_ROW = "reverse"
"""The row of the move picked for playback, full screen."""


def _clip(text: str, width: int) -> str:
    """Cut ``text`` down to ``width`` cells, marking the cut."""
    if cell_len(text) > width:
        return text[: width - 1] + "…"
    return text


def _pad(text: str, width: int) -> str:
    """Pad to ``width`` terminal cells, which ``len`` miscounts for kanji."""
    return text + " " * (width - cell_len(text))


def _super_art_marker(super_art: str, *, equipped: bool) -> str:
    """The gutter each row starts in: blank, or the Super Art it belongs to."""
    if not super_art:
        return " " * SUPER_ART_WIDTH
    return f"{'▸' if equipped else ' '}{super_art:<3} "


CHAIN_MARK = "↳ "
"""What a move that follows on from another is written with. The guides list a
link directly under the move it continues, so the mark plus that position is
the whole explanation: it says "and then this", and the row above says from
what."""


def _move_name(move: Move) -> str:
    """The name as the list writes it, marked if it follows on from another."""
    return f"{CHAIN_MARK}{move.name}" if move.follows else move.name


def _row_style(move: Move, *, equipped: bool, full: bool) -> str:
    """Struck through if untrainable (but never full screen), dim if its Super Art is not equipped."""
    if not move.trainable and not full:
        return "dim strike"
    if not equipped:
        return "dim"
    return CATEGORY_STYLES.get(move.category, "white")


def _highlight(move: Move, *, lit: RecognisableMove | None, cursor: RecognisableMove | None) -> str:
    """Lit for the move that just came out, over marked for the one picked; nothing for the rest."""
    if move is lit:
        return LIT_ROW
    if move is cursor:
        return CURSOR_ROW
    return ""


def listed(character: Character) -> list[Move]:
    """The character's moves in the order the list draws them."""
    return [move for category in _ORDER for move in character.moves if move.category == category]


class MoveList(VerticalScroll):
    """Every move for a character, grouped, with untrainable ones dimmed."""

    can_focus = False
    """Scrolled by the wheel or by the cursor, so the arrow keys stay the trainer's."""

    cursor: RecognisableMove | None = None
    """The move picked for playback, whose row is marked, and scrolled to whenever it moves."""
    _revealed: RecognisableMove | None = None

    DEFAULT_CSS = """
    /* Until the first paint sizes it to its rows; see _fit_width. */
    MoveList {
        width: 52;
        border-left: solid $panel;
        padding: 0 1;
        scrollbar-size-vertical: 1;
    }
    /* A row never wraps: one too long for the list is cut where the list ends.
       Textual goes by this rather than a rich Text's own no_wrap. */
    MoveList #movelist-body { text-wrap: nowrap; text-overflow: ellipsis; }
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
        name_width = max((cell_len(_move_name(move)) for move, _ in rows), default=0) + 2
        command_width = max((cell_len(written) for move, written in rows if written != move.command), default=0) + 2
        # Beside the trainer every input shares the one column, the guide's own
        # words included where the trainer has nothing better to write.
        widest_input = max((cell_len(written) for _, written in rows), default=0)
        name_width = self._fit_width(name_width, widest_input, full=full)

        text = Text()
        cursor_line: int | None = None
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
                    text.append(_pad(_move_name(move), name_width), style=style)
                    text.append(_pad(written, command_width))
                    text.append(move.command if written != move.command else "", style="dim")
                else:
                    # An input too long for the list is cut where the list ends.
                    text.append(_pad(_clip(_move_name(move), name_width - 1), name_width), style=style)
                    text.append(written, style="dim")
                if move is self.cursor:
                    cursor_line = text.plain.count("\n")
                text.stylize(_highlight(move, lit=lit, cursor=self.cursor), start)
                text.append("\n")
            text.append("\n")

        untrainable = sum(1 for move in character.moves if not move.trainable)
        if untrainable and not full:
            text.append(
                f"{untrainable} struck through need context the trainer has no model of\n",
                style="dim italic",
            )
        self.query_one("#movelist-body", Static).update(text)
        self._reveal(cursor_line)

    def _reveal(self, line: int | None) -> None:
        """Scroll the cursor's row into view when it has moved, and leave the scrolling alone otherwise."""
        if self.cursor is not self._revealed and line is not None:
            self.call_after_refresh(self.scroll_to_region, Region(0, line, 1, 1), animate=False)
        self._revealed = self.cursor

    def _fit_width(self, name_width: int, command_width: int, *, full: bool) -> int:
        """Size the list, and say how wide its names may be.

        Full screen, the screen's own CSS spreads it across the width. Beside
        the trainer it is as wide as its rows, up to half the screen and never
        below ``MIN_WIDTH``; short of that the names give way first, since the
        input is what is read.
        """
        if full:
            self.styles.clear_rule("width")
            return name_width
        rows = SUPER_ART_WIDTH + name_width + command_width
        room = max(min(rows, self.app.size.width // 2 - FRAME), MIN_WIDTH - FRAME)
        self.styles.width = room + FRAME
        return max(min(name_width, room - SUPER_ART_WIDTH - command_width), NAME_WIDTH + 1)
