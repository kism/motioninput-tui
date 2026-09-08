"""The Textual application."""

from time import monotonic
from typing import TYPE_CHECKING

from textual.app import App, SystemCommand

from motioninput_tui.config import Config
from motioninput_tui.constants import PROGRAM_NAME_WITH_VERSION
from motioninput_tui.controls.buttons import DEFAULT_SET, arrangement, get_set
from motioninput_tui.controls.layouts import LayoutKind, gamepad_layout, get_layout, with_buttons
from motioninput_tui.games.loader import load_game
from motioninput_tui.games.rulesets import DISPLAY_GAME
from motioninput_tui.notation_styles import Notation
from motioninput_tui.settings import current as current_settings
from motioninput_tui.settings import tuned_game
from motioninput_tui.utils.logger import get_logger

from .keyboard_driver import KeyRelease, ReleaseAwareDriver
from .screens.input_display import InputDisplayScreen
from .screens.input_picker import InputPickerScreen
from .screens.notation import NotationScreen
from .screens.settings import SettingsScreen
from .screens.setup import SetupScreen
from .screens.training import TrainingScreen
from .widgets.settings_list import SettingsList  # ruff: ignore[typing-only-first-party-import] - Textual evaluates the on_settings_list_changed annotation at runtime

if TYPE_CHECKING:
    from collections.abc import Iterable

    from textual.screen import Screen

    from motioninput_tui.controls.buttons import ButtonSet
    from motioninput_tui.controls.layouts import ControlLayout
    from motioninput_tui.engine.recognizer import BufferPolicy
    from motioninput_tui.games.models import Character, Game

logger = get_logger(__name__)

QUIT_CONFIRM_WINDOW_S = 2.0
"""How long a first ctrl+c counts for, before a second one quits."""


class MotionInputApp(App[None]):
    """Move between the input picker, the setup screen and the trainer.

    The :class:`~motioninput_tui.config.Config` passed in doubles as the
    starting selection and as the place the last used one is remembered, so
    every choice made here is written straight back to it.
    """

    TITLE = PROGRAM_NAME_WITH_VERSION
    CSS = """
    Screen { background: $surface; }
    """

    def __init__(self, config: Config | None = None, *, key_release: bool = True, skip_setup: bool = False) -> None:
        """Set up the app.

        ``key_release`` asks the terminal to report key releases; terminals that
        do not understand the request ignore it and the trainer falls back to
        inferring holds from auto-repeat. ``skip_setup`` goes straight to the
        trainer, for when the command line named a game and a character.
        """
        super().__init__(driver_class=ReleaseAwareDriver if key_release else None)
        self.config = config if config is not None else Config()
        self._key_release = key_release
        self._skip_setup = skip_setup
        self._quit_requested_at: float | None = None

    def on_mount(self) -> None:
        """Open the trainer directly if the command line gave a full selection."""
        selection = (self.config.game, self.config.character)
        if self._skip_setup and all(selection):
            self._start(self.config.game or "", self.config.character or "", self.config.layout)
            return
        self._open_input_picker()

    def get_system_commands(self, screen: Screen) -> Iterable[SystemCommand]:
        """Drop the SVG screenshot command; this trainer has no use for it."""
        for command in super().get_system_commands(screen):
            if command.title != "Screenshot":
                yield command

    def action_help_quit(self) -> None:
        """Quit on a second ctrl+c.

        Textual unbinds ctrl+c from quit because it means copy when an input is
        focused, and only shows a hint instead. Nothing here takes text input,
        and ctrl+c is what people press to leave a terminal program, so a second
        press within a couple of seconds really does quit.
        """
        now = monotonic()
        previous = self._quit_requested_at
        if previous is not None and now - previous <= QUIT_CONFIRM_WINDOW_S:
            self.exit()
            return
        self._quit_requested_at = now
        self.notify("Press ctrl+c again to quit.", title="Quit?", timeout=QUIT_CONFIRM_WINDOW_S)

    def on_input_picker_screen_gamepad_bindings_changed(self, event: InputPickerScreen.GamepadBindingsChanged) -> None:
        """Remember the gamepad attack rebinds the player just made."""
        self._remember(gamepad_bindings=event.bindings)

    def action_settings(self) -> None:
        """Open the settings over whatever is running. The trainer's ctrl+b."""
        self.push_screen(SettingsScreen(current_settings(self.config)))

    def action_notation(self) -> None:
        """Open the notation menu over whatever is running. ctrl+n."""
        self.push_screen(NotationScreen(self.config.notation))

    def on_notation_screen_changed(self, event: NotationScreen.Changed) -> None:
        """Remember how moves are to be written, and rewrite any on screen."""
        self._remember(notation=event.choices)
        for screen in self.screen_stack:
            if isinstance(screen, TrainingScreen):
                screen.apply_notation(Notation(event.choices))

    def on_settings_list_changed(self, event: SettingsList.Changed) -> None:
        """Remember a toggled setting, wherever it was toggled.

        Every setting is a boolean attribute of the config, so the map the
        widget sends back can be written straight onto it. A session already
        running takes the change now rather than on the next one.
        """
        self._remember(**event.values)
        for screen in self.screen_stack:
            if isinstance(screen, TrainingScreen):
                screen.apply_settings(tuned_game(screen.session.game, self.config), self.config.buffer_policy)
            elif isinstance(screen, InputDisplayScreen):
                session = screen.session
                screen.apply_panel(*self._panel_for(session.game, screen.character, session.layout.key))

    def on_key_release(self, event: KeyRelease) -> None:
        """Route a key release to the trainer.

        Releases are not Textual Key events, so they do not reach a screen on
        their own; nothing else in the app has any use for them.
        """
        screen = self.screen
        if isinstance(screen, TrainingScreen | InputDisplayScreen):
            screen.handle_release(event.key)

    def _remember(self, **changes: object) -> None:
        """Update the config and write it, ignoring any failure to do so."""
        for field, value in changes.items():
            setattr(self.config, field, value)
        self.config.save()

    def _open_input_picker(self) -> None:
        """Ask what the player is on, then move on to what they are training."""

        def on_done(layout_key: str | None) -> None:
            if layout_key is None:  # Dismissed without a choice; nothing sits behind it.
                self.exit()
                return
            self._remember(layout=layout_key)
            self._open_setup()

        self.push_screen(
            InputPickerScreen(self.config.layout, gamepad_bindings=self.config.gamepad_bindings),
            on_done,
        )

    def _open_setup(self, *, focus_characters: bool = False) -> None:
        def on_done(result: tuple[str, str] | None) -> None:
            if result is None:
                # Escape here is about changing input device, not leaving.
                self._open_input_picker()
                return
            self._start(*result, self.config.layout)

        self.push_screen(
            SetupScreen(
                (self.config.game, self.config.character),
                settings=current_settings(self.config),
                layout_name=get_layout(self.config.layout).name,
                focus_characters=focus_characters,
            ),
            on_done,
        )

    def _buttons_for(self, game: Game, character: Character) -> ButtonSet:
        """The panel to play this on.

        Every game names its own set; the input display is the one where the
        player picks it, which is what its characters are.
        """
        chosen = get_set(character.key) if game.key == DISPLAY_GAME else game.buttons
        return arrangement(chosen, slanted_neo_geo=self.config.neo_geo_slant)

    def _panel_for(self, game: Game, character: Character, layout_key: str) -> tuple[ControlLayout, ButtonSet]:
        """The layout with this game's buttons on its attack positions.

        Every layout already carries the Street Fighter six, rebinds included,
        so only another set has to be laid out; that also keeps a rebound pad
        from being flattened back to its defaults.
        """
        layout = get_layout(layout_key)
        if layout.kind is LayoutKind.GAMEPAD:
            layout = gamepad_layout(self.config.gamepad_bindings or None)
        buttons = self._buttons_for(game, character)
        if buttons is not DEFAULT_SET:
            layout = with_buttons(layout, buttons)
        return layout, buttons

    def _start(self, game_key: str, character_key: str, layout_key: str) -> None:
        game = tuned_game(load_game(game_key), self.config)
        character = game.character(character_key)
        layout, buttons = self._panel_for(game, character, layout_key)
        self._remember(game=game.key, character=character.key, layout=layout.key)

        def on_done(_result: None) -> None:
            # Leaving is nearly always about picking someone, or something, else.
            self._open_setup(focus_characters=True)

        if game.key == DISPLAY_GAME:
            display = InputDisplayScreen(game, character, layout, buttons, exact_input=self._key_release)
            self.push_screen(display, on_done)
            return

        policy: BufferPolicy = self.config.buffer_policy
        screen = TrainingScreen(game, character, layout, exact_input=self._key_release, policy=policy)
        screen.apply_notation(Notation(self.config.notation))
        self.push_screen(screen, on_done)
