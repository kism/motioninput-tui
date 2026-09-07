"""Startup screen: pick a control layout, a game and a character."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from rich.text import Text
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, OptionList, Static

from motioninput_tui.controls.layouts import available_layouts
from motioninput_tui.games.loader import available_games
from motioninput_tui.terminal import detect

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from motioninput_tui.controls.layouts import ControlLayout
    from motioninput_tui.games.models import Game


class SetupScreen(Screen):
    """Choose what to train before dropping into the trainer."""

    BINDINGS: ClassVar = [
        Binding("enter", "start", "Start training", priority=True),
        Binding("ctrl+c", "quit", "Quit"),
    ]

    DEFAULT_CSS = """
    SetupScreen { layout: vertical; }
    #warning { padding: 0 2; color: $warning; height: auto; }
    #blurb { padding: 1 2 0 2; height: auto; }
    #columns { height: 1fr; padding: 1 1; }
    #columns > Vertical { width: 1fr; padding: 0 1; }
    #columns Label { text-style: bold; }
    #columns OptionList { height: 1fr; border: solid $panel; }
    #detail { height: 5; padding: 0 2; color: $text-muted; }
    """

    def __init__(self) -> None:
        """Load the rosters and detect the terminal up front."""
        super().__init__()
        self.games = available_games()
        self.layouts = available_layouts()
        self.terminal = detect()

    def compose(self) -> ComposeResult:
        """Build the three pickers."""
        yield Header()
        yield Static(
            Text.from_markup(
                "Motion input trainer. Pick a [b]layout[/b], a [b]game[/b] and a [b]character[/b], "
                "then press [b]enter[/b]."
            ),
            id="blurb",
        )
        if self.terminal.should_warn:
            yield Static(Text(f"⚠ {self.terminal.warning()}"), id="warning")

        with Horizontal(id="columns"):
            with Vertical():
                yield Label("Layout")
                yield OptionList(*[layout.name for layout in self.layouts], id="layouts")
            with Vertical():
                yield Label("Game")
                yield OptionList(*[game.short_name for game in self.games], id="games")
            with Vertical():
                yield Label("Character")
                yield OptionList(id="characters")
        yield Static(id="detail")
        yield Footer()

    def on_mount(self) -> None:
        """Select sensible defaults and focus the layout picker."""
        self.title = "motioninput-tui"
        self.sub_title = f"{self.terminal.name} ({self.terminal.speed})"
        if not self.games:
            self.query_one("#detail", Static).update(
                Text("No roster data found. Run: python -m motioninput_tui.datagen", style="bold red")
            )
            return
        self.query_one("#layouts", OptionList).highlighted = 0
        games = self.query_one("#games", OptionList)
        games.highlighted = 0
        self._load_characters(0)
        self.query_one("#layouts", OptionList).focus()

    def _load_characters(self, game_index: int) -> None:
        characters = self.query_one("#characters", OptionList)
        characters.clear_options()
        game = self.games[game_index]
        characters.add_options([character.name for character in game.characters])
        if game.characters:
            characters.highlighted = 0
        self._describe()

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        """Keep the character list and the blurb in step with the selection."""
        if event.option_list.id == "games":
            self._load_characters(event.option_index)
        self._describe()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Enter on any list starts training."""
        if event.option_list.id in {"layouts", "games"}:
            self._focus_next_picker(event.option_list.id)
            return
        self.action_start()

    def _focus_next_picker(self, current: str) -> None:
        order = {"layouts": "#games", "games": "#characters"}
        self.query_one(order[current], OptionList).focus()

    def _selection(self) -> tuple[ControlLayout, Game, str] | None:
        if not self.games:
            return None
        layout_index = self.query_one("#layouts", OptionList).highlighted or 0
        game_index = self.query_one("#games", OptionList).highlighted or 0
        character_index = self.query_one("#characters", OptionList).highlighted or 0
        game = self.games[game_index]
        if not game.characters:
            return None
        return self.layouts[layout_index], game, game.characters[character_index].key

    def _describe(self) -> None:
        selection = self._selection()
        if selection is None:
            return
        layout, game, _ = selection
        text = Text()
        text.append(f"{layout.description}\n", style="bold")
        text.append(f"Move: {layout.movement_help()}    Attack: {layout.attack_help()}\n")
        text.append(f"{game.name}: {game.notes[0] if game.notes else ''}", style="italic")
        self.query_one("#detail", Static).update(text)

    def action_start(self) -> None:
        """Hand the selection back to the app."""
        selection = self._selection()
        if selection is None:
            return
        layout, game, character_key = selection
        self.dismiss((game.key, character_key, layout.key))
