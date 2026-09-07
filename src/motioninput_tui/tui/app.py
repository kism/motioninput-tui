"""The Textual application."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import App

from motioninput_tui.config import Config
from motioninput_tui.constants import PROGRAM_NAME_WITH_VERSION
from motioninput_tui.controls.layouts import get_layout
from motioninput_tui.games.loader import load_game
from motioninput_tui.utils.logger import get_logger

from .keyboard_driver import KeyRelease, ReleaseAwareDriver
from .screens.setup import SetupScreen
from .screens.training import TrainingScreen

if TYPE_CHECKING:
    from motioninput_tui.engine.recognizer import BufferPolicy

logger = get_logger(__name__)


class MotionInputApp(App[None]):
    """Move between the setup screen and the trainer.

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

    def on_mount(self) -> None:
        """Open the trainer directly if the command line gave a full selection."""
        selection = (self.config.game, self.config.character)
        if self._skip_setup and all(selection):
            self._start(self.config.game or "", self.config.character or "", self.config.layout)
            return
        self._open_setup()

    def on_training_screen_policy_changed(self, event: TrainingScreen.PolicyChanged) -> None:
        """Remember the buffer rule the player just toggled to."""
        self._remember(buffer_policy=event.policy)

    def on_key_release(self, event: KeyRelease) -> None:
        """Route a key release to the trainer.

        Releases are not Textual Key events, so they do not reach a screen on
        their own; nothing else in the app has any use for them.
        """
        screen = self.screen
        if isinstance(screen, TrainingScreen):
            screen.handle_release(event.key)

    def _remember(self, **changes: object) -> None:
        """Update the config and write it, ignoring any failure to do so."""
        for field, value in changes.items():
            setattr(self.config, field, value)
        self.config.save()

    def _open_setup(self) -> None:
        def on_done(result: tuple[str, str, str] | None) -> None:
            if result is None:
                self.exit()
                return
            self._start(*result)

        initial = (self.config.game, self.config.character, self.config.layout)
        self.push_screen(SetupScreen(initial), on_done)

    def _start(self, game_key: str, character_key: str, layout_key: str) -> None:
        game = load_game(game_key)
        character = game.character(character_key)
        layout = get_layout(layout_key)
        self._remember(game=game.key, character=character.key, layout=layout.key)

        def on_done(_result: None) -> None:
            self._open_setup()

        policy: BufferPolicy = self.config.buffer_policy
        self.push_screen(
            TrainingScreen(game, character, layout, exact_input=self._key_release, policy=policy),
            on_done,
        )
