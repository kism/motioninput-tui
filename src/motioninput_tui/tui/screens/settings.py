"""Every option in one modal: the settings, and how moves are written.

Sections down the left, their choices on the right: the settings' toggles, or
one family of motions with every way of writing it drawn as its own preview,
since picking one is a matter of taste and of what your font has. The line
underneath explains the highlighted setting, or writes a few moves out with the
whole set of notation choices.

Opened over a session, the game's own notes head it, which is the one place
they are shown. The app applies whatever changes to whatever is running.
"""

from typing import TYPE_CHECKING, ClassVar, override

from rich.cells import cell_len
from rich.text import Text
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Footer, Label, OptionList, Static

from motioninput_tui.engine.motions import MotionKind, MotionSpec
from motioninput_tui.engine.notation import ANY_KICK, ANY_PUNCH
from motioninput_tui.notation_styles import FAMILY_NAMES, STYLES, Family, Notation
from motioninput_tui.tui.widgets.settings_list import SettingsList

from .base import AppScreen

if TYPE_CHECKING:
    from collections.abc import Mapping

    from textual.app import ComposeResult

    from motioninput_tui.games.models import Game
    from motioninput_tui.notation_styles import Style

GENERAL = "General"
"""The first section, the toggles. Every one after it is a family of motions."""

_FAMILIES: tuple[Family, ...] = tuple(FAMILY_NAMES)

_SAMPLES: tuple[tuple[str, MotionSpec], ...] = (
    ("Fireball", MotionSpec(kind=MotionKind.QCF, buttons=ANY_PUNCH)),
    ("Dragon punch", MotionSpec(kind=MotionKind.DP, buttons=ANY_PUNCH)),
    ("Super", MotionSpec(kind=MotionKind.QCF_X2, buttons=ANY_KICK)),
)
"""Moves written out under the whole set of choices, not just one family's."""

STYLE_NAME_WIDTH = 16


class SettingsScreen(AppScreen[None], ModalScreen[None]):
    """Toggle settings and pick how moves are written, over whatever is underneath."""

    BINDINGS: ClassVar = [
        # The toggles take space for themselves; on the other lists it acts on the row.
        Binding("space", "pick", "Pick"),
        # Priority, or the lists' own hidden sideways scrolling takes these keys'
        # place in the footer. Only the one that goes somewhere is shown; see check_action.
        Binding("left", "sections", "Sections", priority=True),
        Binding("right", "choices", "Choices", priority=True),
        Binding("escape,ctrl+b", "close", "Done"),
        # Space picks, so enter just confirms, as it does on every screen.
        Binding("enter", "close", "Done", priority=True, show=False),
    ]

    class NotationChanged(Message):
        """Posted when a style is picked, with every family's choice."""

        def __init__(self, choices: dict[str, str]) -> None:
            """Carry the choices keyed by family, as the config stores them."""
            super().__init__()
            self.choices = choices

    DEFAULT_CSS = """
    SettingsScreen { align: center middle; }
    /* Scrolls only when a game's notes make it taller than the terminal. */
    SettingsScreen > VerticalScroll {
        width: 80; height: auto; max-height: 100%; padding: 1 2;
        background: $surface; border: thick $primary;
    }
    SettingsScreen #title { width: 100%; text-align: center; text-style: bold; }
    SettingsScreen #game { width: 100%; height: auto; margin-bottom: 1; }
    SettingsScreen #columns { height: 10; }
    SettingsScreen #columns OptionList { border: none; background: $surface; }
    SettingsScreen #sections { width: 20; }
    SettingsScreen SettingsList, SettingsScreen #styles { width: 1fr; }
    SettingsScreen #detail { width: 100%; height: 3; color: $text-muted; }
    """

    def __init__(
        self, values: Mapping[str, bool], choices: Mapping[str, str] | None = None, *, game: Game | None = None
    ) -> None:
        """Open on every setting's value, keyed by config attribute, and the notation in force.

        ``game`` is the one a session is running, whose notes head the menu.
        """
        super().__init__()
        self._values = dict(values)
        self.notation = Notation(dict(choices or {}))
        self._game = game

    @override
    def compose(self) -> ComposeResult:
        """The game's notes, the sections beside their choices, and the line explaining them."""
        with VerticalScroll(can_focus=False):  # out of the tab order; the lists scroll it to themselves
            yield Label("Settings", id="title")
            if self._game is not None:
                yield Static(_about(self._game), id="game")
            with Horizontal(id="columns"):
                yield OptionList(GENERAL, *[FAMILY_NAMES[family] for family in _FAMILIES], id="sections")
                yield SettingsList(self._values)
                yield OptionList(id="styles")
            yield Label(id="detail")
        yield Footer()

    def on_mount(self) -> None:
        """Start on the toggles, so ctrl+b and space flips a setting as it always has."""
        self._show_section()
        self.query_one(SettingsList).focus()

    @property
    def _family(self) -> Family | None:
        """The family of motions on the right, or None for the toggles."""
        index = self.query_one("#sections", OptionList).highlighted or 0
        return _FAMILIES[index - 1] if index else None

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        """Moving down the sections swaps what is beside them; moving in them re-explains."""
        if event.option_list.id == "sections":
            self._show_section()
        else:
            self._describe()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Space or a click takes a style, or crosses from a section into it.

        The toggles never get here: they take their own selections.
        """
        if event.option_list.id == "sections":
            self.action_choices()
        elif event.option_list.id == "styles":
            self._choose(event.option_index)

    def on_settings_list_changed(self, _event: SettingsList.Changed) -> None:
        """Keep the explanation in step. The app saves it as this bubbles past."""
        self._describe()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        """Offer left from the choices and right from the sections, never both.

        False hides the other one, where None would show it greyed out.
        """
        del parameters
        on_sections = self.focused is self.query_one("#sections", OptionList)
        if action == "sections":
            return not on_sections
        if action == "choices":
            return on_sections
        return True

    def action_pick(self) -> None:
        """Space: act on the highlighted row of whichever list has focus."""
        focused = self.focused
        if isinstance(focused, OptionList):
            focused.action_select()

    def action_sections(self) -> None:
        """Left: back out to the sections."""
        self.query_one("#sections", OptionList).focus()

    def action_choices(self) -> None:
        """Right: into the highlighted section's choices."""
        choices = self.query_one(SettingsList) if self._family is None else self.query_one("#styles", OptionList)
        choices.focus()

    def _show_section(self) -> None:
        family = self._family
        self.query_one(SettingsList).display = family is None
        self.query_one("#styles", OptionList).display = family is not None
        if family is not None:
            self._render_styles(family)
        self._describe()

    def _choose(self, index: int) -> None:
        """Take the style at ``index`` for the family being looked at."""
        family = self._family
        if family is None or index >= len(STYLES[family]):
            return
        self.notation = self.notation.with_style(family, STYLES[family][index])
        self._render_styles(family)
        self._describe()
        self.post_message(self.NotationChanged(dict(self.notation.choices)))

    def _render_styles(self, family: Family) -> None:
        """Redraw the style list for ``family``, each row a preview."""
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

    def _describe(self) -> None:
        """The highlighted setting explained, or a few moves written with every notation choice."""
        text = Text()
        if self._family is None:
            pane = self.query_one(SettingsList)
            setting = pane.highlighted_setting
            if setting is not None:
                state = "on" if pane.is_on(setting) else "off"
                text.append(f"{setting.name}: {state}\n", style="bold")
                text.append(setting.detail)
        else:
            for index, (name, spec) in enumerate(_SAMPLES):
                if index:
                    text.append("    ")
                text.append(f"{name} ", style="dim")
                text.append(self.notation.write(spec))
        self.query_one("#detail", Label).update(text)

    def action_close(self) -> None:
        """Leave; every change has already been applied and saved."""
        self.dismiss(None)


def _about(game: Game) -> Text:
    """The game's name and its notes: how its rules differ from the other games'."""
    text = Text(game.name, style="bold")
    for note in game.notes:
        text.append(f"\n• {note}", style="italic")
    return text
