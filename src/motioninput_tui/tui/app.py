"""The Textual application."""

from __future__ import annotations

from motioninput_tui.constants import PROGRAM_NAME_WITH_VERSION
from motioninput_tui.controls.layouts import get_layout
from motioninput_tui.games.loader import load_game
from motioninput_tui.utils.logger import get_logger

from .screens.setup import SetupScreen
from .screens.training import TrainingScreen

logger = get_logger(__name__)

try:  # pragma: no cover - textual is a hard dependency, this is only for clarity
    from textual.app import App
except ImportError as exc:  # pragma: no cover
    message = "textual is required to run the trainer. Try: uv sync"
    raise SystemExit(message) from exc


class MotionInputApp(App[None]):
    """Move between the setup screen and the trainer."""

    TITLE = PROGRAM_NAME_WITH_VERSION
    CSS = """
    Screen { background: $surface; }
    """

    def __init__(self, game: str | None = None, character: str | None = None, layout: str | None = None) -> None:
        """Optionally skip the setup screen when everything is given up front."""
        super().__init__()
        self._preset = (game, character, layout)

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

        self.push_screen(TrainingScreen(game, character, layout), on_done)
