"""Second screen: settings, a game and a character.

The input device is chosen before this, on
:class:`~motioninput_tui.tui.screens.input_picker.InputPickerScreen`, so the
three panes here are all about what to train: the player's own settings, which
sit above every game's rules, then the game and the character.
"""

from typing import TYPE_CHECKING, ClassVar

from rich.text import Text
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, OptionList, Static

from motioninput_tui.games.loader import available_games
from motioninput_tui.tui.widgets.settings_list import SettingsList

if TYPE_CHECKING:
    from collections.abc import Mapping

    from textual.app import ComposeResult

    from motioninput_tui.games.models import Game


class SetupScreen(Screen["tuple[str, str] | None"]):
    """Choose what to train. Dismisses with (game, character), or None to go back."""

    BINDINGS: ClassVar = [
        Binding("enter", "select", "Start training", priority=True),
        Binding("escape", "back", "Change input"),
        Binding("ctrl+n", "app.notation", "Notation"),
        Binding("ctrl+q", "quit", "Quit"),
        # Nothing here takes text input, so drop Screen's copy/paste bindings
        # from the key panel; ctrl+c stays as the quit shortcut.
        Binding("ctrl+c,super+c", "app.help_quit", show=False, system=True),
    ]

    DEFAULT_CSS = """
    SetupScreen { layout: vertical; }
    SetupScreen #blurb { padding: 1 2 0 2; height: auto; }
    SetupScreen #columns { height: 1fr; padding: 1 1; }
    SetupScreen #columns > Vertical { width: 1fr; padding: 0 1; }
    SetupScreen #columns Label { text-style: bold; }
    SetupScreen #columns OptionList { height: 1fr; border: solid $panel; }
    SetupScreen #detail { height: 5; padding: 0 2; color: $text-muted; }
    """

    def __init__(
        self,
        initial: tuple[str | None, str | None] = (None, None),
        *,
        settings: Mapping[str, bool] | None = None,
        layout_name: str = "",
        focus_characters: bool = False,
    ) -> None:
        """Load the rosters and take the settings as they stand.

        ``initial`` is the (game, character) used last time, so the pickers open
        on it rather than always on the first entry. ``settings`` is every
        setting's current value, keyed by config attribute. ``layout_name``
        names the input device chosen on the way in, which is all this screen
        does with it. ``focus_characters`` starts on the character list instead
        of the settings one, for coming back from the trainer, where changing
        character is almost always the reason for leaving.
        """
        super().__init__()
        self.games = available_games()
        self._settings = dict(settings or {})
        self._initial = initial
        self._layout_name = layout_name
        self._focus_characters = focus_characters
        self._loaded_game: int | None = None

    def compose(self) -> ComposeResult:
        """Build the three panes."""
        yield Header()
        yield Static(
            Text.from_markup(
                "Set your [b]options[/b] with [b]space[/b], pick a [b]game[/b] and a "
                "[b]character[/b], then press [b]enter[/b]."
            ),
            id="blurb",
        )
        with Horizontal(id="columns"):
            with Vertical():
                yield Label("Settings")
                yield SettingsList(self._settings)
            with Vertical():
                yield Label("Game")
                yield OptionList(*[game.short_name for game in self.games], id="games")
            with Vertical():
                yield Label("Character")
                yield OptionList(id="characters")
        yield Static(id="detail")
        yield Footer()

    def on_mount(self) -> None:
        """Open the pickers where they left off."""
        self.title = "motioninput-tui"
        self.sub_title = self._layout_name or "What are you training?"
        if not self.games:
            self.query_one("#detail", Static).update(
                Text("No roster data found. Run: python -m motioninput_tui.datagen", style="bold red")
            )
            return
        # An OptionList highlights its first entry when options are added and
        # posts an event for it, so the last used selection has to wait until
        # those have been dealt with or it gets overwritten. Focus waits with
        # it, since the character list is empty until then.
        self.call_after_refresh(self._apply_initial)

    def _apply_initial(self) -> None:
        """Open the pickers on whatever was used last time."""
        game_key, character_key = self._initial
        game_index = _index_of([game.key for game in self.games], game_key)
        self.query_one("#games", OptionList).highlighted = game_index
        self._load_characters(game_index, character_key)
        self._focus_picker()

    def _focus_picker(self) -> None:
        """Start on the character list when asked, or the settings one otherwise."""
        characters = self.query_one("#characters", OptionList)
        if self._focus_characters and characters.option_count:
            characters.focus()
            return
        self.query_one(SettingsList).focus()

    def _load_characters(self, game_index: int, character_key: str | None = None) -> None:
        self._loaded_game = game_index
        characters = self.query_one("#characters", OptionList)
        characters.clear_options()
        game = self.games[game_index]
        characters.add_options([character.name for character in game.characters])
        if game.characters:
            characters.highlighted = _index_of([entry.key for entry in game.characters], character_key)
        self._describe()

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        """Keep the character list and the blurb in step with the selection.

        Setting a game on mount queues a highlight event that arrives after
        the character has been pre-selected, so a game that is already loaded
        is ignored rather than resetting the character back to the first one.
        """
        if event.option_list.id == "games" and event.option_index != self._loaded_game:
            self._load_characters(event.option_index)
        self._describe()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """A click starts training, or moves on from the game pane.

        The settings pane never gets here: it takes its own selections.
        """
        if event.option_list.id == "games":
            self.query_one("#characters", OptionList).focus()
        else:
            self.action_start()

    def action_select(self) -> None:
        """Enter: move on from a game, or start training.

        Settings are flipped with space, so enter means the same on that pane
        as it does on the character list.
        """
        if self.query_one("#games", OptionList).has_focus:
            self.query_one("#characters", OptionList).focus()
        else:
            self.action_start()

    def on_settings_list_changed(self, _event: SettingsList.Changed) -> None:
        """Keep the description in step. The app saves it as this bubbles past."""
        self._describe()

    def _selection(self) -> tuple[Game, str] | None:
        if not self.games:
            return None
        game_index = self.query_one("#games", OptionList).highlighted or 0
        character_index = self.query_one("#characters", OptionList).highlighted or 0
        game = self.games[game_index]
        if not game.characters:
            return None
        return game, game.characters[character_index].key

    def _describe(self) -> None:
        """Explain the highlighted setting, then the highlighted game."""
        text = Text()
        pane = self.query_one(SettingsList)
        setting = pane.highlighted_setting
        if setting is not None:
            state = "on" if pane.is_on(setting) else "off"
            text.append(f"{setting.name}: {state}\n", style="bold")
            text.append(f"{setting.detail}\n")
        selection = self._selection()
        if selection is not None:
            game, _ = selection
            text.append(f"{game.name}: {game.notes[0] if game.notes else ''}", style="italic")
        self.query_one("#detail", Static).update(text)

    def action_start(self) -> None:
        """Hand the selection back to the app."""
        selection = self._selection()
        if selection is None:
            return
        game, character_key = selection
        self.dismiss((game.key, character_key))

    def action_back(self) -> None:
        """Return to the input picker."""
        self.dismiss(None)


def _index_of(keys: list[str], wanted: str | None) -> int:
    """Where ``wanted`` sits in ``keys``, or the first entry if it is gone."""
    if wanted is not None and wanted in keys:
        return keys.index(wanted)
    return 0
