"""The Textual application."""

from __future__ import annotations

from textual.app import App

from motioninput_tui.constants import PROGRAM_NAME_WITH_VERSION
from motioninput_tui.controls.layouts import get_layout
from motioninput_tui.games.loader import load_game
from motioninput_tui.utils.logger import get_logger

from .keyboard_driver import KeyRelease, ReleaseAwareDriver
from .screens.setup import SetupScreen
from .screens.training import TrainingScreen

logger = get_logger(__name__)


class MotionInputApp(App[None]):
    """Move between the setup screen and the trainer."""

    TITLE = PROGRAM_NAME_WITH_VERSION
    CSS = """
    Screen { background: $surface; }
    """

    def __init__(
        self,
        game: str | None = None,
        character: str | None = None,
        layout: str | None = None,
        *,
        key_release: bool = True,
    ) -> None:
        """Optionally skip the setup screen when everything is given up front.

        ``key_release`` asks the terminal to report key releases. Terminals that
        do not understand the request ignore it and the trainer falls back to
        inferring holds from auto-repeat.
        """
        super().__init__(driver_class=ReleaseAwareDriver if key_release else None)
        self._preset = (game, character, layout)
        self._key_release = key_release

    def on_key_release(self, event: KeyRelease) -> None:
        """Route a key release to the trainer.

        Releases are not Textual Key events, so they do not reach a screen on
        their own; nothing else in the app has any use for them.
        """
        screen = self.screen
        if isinstance(screen, TrainingScreen):
            screen.handle_release(event.key)

    def on_mount(self) -> None:
        """Open the trainer directly if the CLI gave a full selection."""
        game, character, layout = self._preset
        if game and character:
            self._start(game, character, layout or "hitbox")
            return
        self._open_setup()

    def _open_setup(self) -> None:
        def on_done(result: tuple[str, str, str] | None) -> None:
            if result is None:
                self.exit()
                return
            self._start(*result)

        self.push_screen(SetupScreen(), on_done)

    def _start(self, game_key: str, character_key: str, layout_key: str) -> None:
        game = load_game(game_key)
        character = game.character(character_key)
        layout = get_layout(layout_key)

        def on_done(_result: None) -> None:
            self._open_setup()

        self.push_screen(TrainingScreen(game, character, layout, exact_input=self._key_release), on_done)
