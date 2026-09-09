"""The second options menu: how moves are written.

A motion on the left, the ways of writing it on the right, each row drawn in
the style it offers. Picking one is a matter of taste and of what your font
has, so every row is its own preview and the line underneath shows a move
written out with the whole set of choices.
"""

from typing import TYPE_CHECKING, ClassVar, override

from rich.cells import cell_len
from rich.text import Text
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Footer, Label, OptionList

from motioninput_tui.engine.motions import MotionKind, MotionSpec
from motioninput_tui.engine.notation import ANY_KICK, ANY_PUNCH
from motioninput_tui.notation_styles import FAMILY_NAMES, STYLES, Family, Notation

if TYPE_CHECKING:
    from collections.abc import Mapping

    from textual.app import ComposeResult

    from motioninput_tui.notation_styles import Style

_FAMILIES: tuple[Family, ...] = tuple(FAMILY_NAMES)

_SAMPLES: tuple[tuple[str, MotionSpec], ...] = (
    ("Fireball", MotionSpec(kind=MotionKind.QCF, buttons=ANY_PUNCH)),
    ("Dragon punch", MotionSpec(kind=MotionKind.DP, buttons=ANY_PUNCH)),
    ("Super", MotionSpec(kind=MotionKind.QCF_X2, buttons=ANY_KICK)),
)
"""Moves written out under the whole set of choices, not just one family's."""

STYLE_NAME_WIDTH = 16


class NotationScreen(ModalScreen[None]):
    """Pick how each family of motions is written."""

    BINDINGS: ClassVar = [
        Binding("escape,ctrl+n", "close", "Done"),
        # Nothing here takes text input, so drop Screen's copy/paste bindings
        # from the key panel; ctrl+c stays as the quit shortcut.
        Binding("ctrl+c", "app.help_quit", show=False, system=True),
    ]

    class Changed(Message):
        """Posted when a style is picked, with every family's choice."""

        def __init__(self, choices: dict[str, str]) -> None:
            """Carry the choices keyed by family, as the config stores them."""
            super().__init__()
            self.choices = choices

    DEFAULT_CSS = """
    NotationScreen { align: center middle; }
    NotationScreen > Vertical {
        width: 76; height: auto; padding: 1 2;
        background: $surface; border: thick $primary;
    }
    NotationScreen #title { width: 100%; text-align: center; text-style: bold; }
    NotationScreen #columns { height: 9; }
    NotationScreen #families { width: 24; border: none; background: $surface; }
    NotationScreen #styles { width: 1fr; border: none; background: $surface; }
    NotationScreen #sample { width: 100%; height: 2; color: $text-muted; }
    """

    def __init__(self, choices: Mapping[str, str] | None = None) -> None:
        """Open on the notation in force."""
        super().__init__()
        self.notation = Notation(dict(choices or {}))

    @override
    def compose(self) -> ComposeResult:
        """Motions on the left, their styles on the right, a sample underneath."""
        with Vertical():
            yield Label("Move notation", id="title")
            with Horizontal(id="columns"):
                yield OptionList(*[FAMILY_NAMES[family] for family in _FAMILIES], id="families")
                yield OptionList(id="styles")
            yield Label(id="sample")
        yield Footer()

    def on_mount(self) -> None:
        """Start on the motion list; the style list follows it."""
        self._render_styles()
        self._render_sample()
        self.query_one("#families", OptionList).focus()

    @property
    def _family(self) -> Family:
        index = self.query_one("#families", OptionList).highlighted or 0
        return _FAMILIES[index]

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        """Moving down the motions swaps the styles listed beside them."""
        if event.option_list.id == "families":
            self._render_styles()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Enter takes a style, or crosses from the motions to them."""
        if event.option_list.id == "families":
            self.query_one("#styles", OptionList).focus()
            return
        self._choose(event.option_index)

    def _choose(self, index: int) -> None:
        """Take the style at ``index`` for the family being looked at."""
        family = self._family
        styles = STYLES[family]
        if index >= len(styles):
            return
        self.notation = self.notation.with_style(family, styles[index])
        self._render_styles()
        self._render_sample()
        self.post_message(self.Changed(dict(self.notation.choices)))

    def _render_styles(self) -> None:
        """Redraw the style list for the highlighted motion, each row a preview."""
        family = self._family
        styles = STYLES[family]
        current = self.notation.style(family)
        pane = self.query_one("#styles", OptionList)
        pane.clear_options()
        pane.add_options([self._row(family, style, taken=style is current) for style in styles])
        pane.highlighted = styles.index(current)

    def _row(self, family: Family, style: Style, *, taken: bool) -> Text:
        mark = Text("[✓] " if taken else "[ ] ")
        # Padded by cell width, not by character count: a name with a kanji in
        # it is wider on screen than it is long, and the previews must line up.
        gap = " " * max(1, STYLE_NAME_WIDTH - cell_len(style.name))
        return mark + Text(style.name + gap) + Text(self.notation.preview(family, style), style="bold")

    def _render_sample(self) -> None:
        """A few moves as they would read with every choice applied."""
        text = Text()
        for index, (name, spec) in enumerate(_SAMPLES):
            if index:
                text.append("    ")
            text.append(f"{name} ", style="dim")
            text.append(self.notation.write(spec))
        self.query_one("#sample", Label).update(text)

    def action_close(self) -> None:
        """Leave; every choice has already been applied and saved."""
        self.dismiss(None)
