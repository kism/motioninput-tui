"""The input display: the game's panel, and every motion the game has.

It is the first character of every roster, and runs on the same
:class:`~motioninput_tui.engine.session.TrainingSession` as the trainer, so
directions are cleaned and holds inferred exactly as they are when a move is on
the line. Its moves are every motion in the game on any button (see
:mod:`motioninput_tui.games.loader`), so what the stick makes is drawn over the
history whoever's move it would be.
"""

from typing import TYPE_CHECKING, ClassVar, override

from rich.cells import cell_len
from rich.text import Text
from textual.binding import Binding
from textual.containers import Center, Horizontal, ItemGrid
from textual.screen import Screen
from textual.widgets import Footer, Static

from motioninput_tui.engine.motions import MotionKind
from motioninput_tui.engine.recognizer import BufferPolicy
from motioninput_tui.engine.session import Outcome, TrainingSession
from motioninput_tui.games.loader import INPUT_DISPLAY
from motioninput_tui.notation_styles import DEFAULT as DEFAULT_NOTATION
from motioninput_tui.tui.widgets.input_strip import InputStrip, trail_brackets
from motioninput_tui.tui.widgets.panel import LIT, ButtonPads, DirectionGate

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from motioninput_tui.controls.buttons import ButtonSet
    from motioninput_tui.controls.layouts import ControlLayout
    from motioninput_tui.games.models import Game
    from motioninput_tui.notation_styles import Notation

TICK_HZ = 60

MOTION_ROWS = 3
"""Lines of motions over the history."""

MOTION_GAP = 3
"""Cells between one column of the motion list and the next."""


class InputDisplayScreen(Screen):
    """Draws the panel live: the gate, the buttons, and the input history under the motions it made."""

    notation: Notation

    BINDINGS: ClassVar = [
        Binding("escape", "back", "Change character"),
        Binding("ctrl+r", "reset", "Reset"),
        Binding("ctrl+b", "app.settings", "Settings"),
        Binding("ctrl+n", "app.notation", "Notation"),
        # Nothing here takes text input, so drop Screen's copy/paste bindings
        # from the key panel; ctrl+c stays as the quit shortcut.
        Binding("ctrl+c", "app.help_quit", show=False, system=True),
    ]

    DEFAULT_CSS = """
    InputDisplayScreen { layout: vertical; }
    InputDisplayScreen #banner { height: auto; padding: 0 1; background: $panel; }
    InputDisplayScreen #motions { border: round $panel; padding: 0 1; }
    InputDisplayScreen #panel-area { height: 1fr; align: center middle; }
    InputDisplayScreen #panel { width: auto; height: auto; }
    InputDisplayScreen InputStrip { height: auto; border-bottom: none; }
    InputDisplayScreen #status { height: auto; padding: 0 1; color: $text-muted; border-top: solid $panel; }
    """

    def __init__(
        self,
        game: Game,
        layout: ControlLayout,
        buttons: ButtonSet,
        *,
        exact_input: bool = False,
        policy: BufferPolicy = BufferPolicy.CONSUME,
    ) -> None:
        """Set a session up on the game's input display.

        ``buttons`` is the game's set as the settings arrange it, which is what
        actually gets drawn.
        """
        super().__init__()
        display = game.character(INPUT_DISPLAY)
        self.session = TrainingSession(game, display, layout, exact_input=exact_input, policy=policy)
        self.panel = buttons
        self.notation = DEFAULT_NOTATION
        order = list(MotionKind)
        self.motions = sorted({move.motion.kind for move in display.moves if move.motion is not None}, key=order.index)
        """Every motion the game has, once each, in the order the engine lists them."""
        self._written: list[str] = []
        """The same, in the player's notation."""

    @override
    def compose(self) -> ComposeResult:
        """The game's motions, then the gate and the buttons side by side, over the input history."""
        yield Static(id="banner")
        motions = ItemGrid(*(Static() for _ in self.motions), id="motions")
        motions.border_title = "Motions"
        yield motions
        with Center(id="panel-area"), Horizontal(id="panel"):
            yield DirectionGate()
            yield ButtonPads()
        yield InputStrip(id="strip")
        yield Static(id="status")
        yield Footer()

    def on_mount(self) -> None:
        """Paint the chrome and start the tick that expires holds."""
        self.title = f"{self.session.game.short_name} · Input display"
        self.sub_title = self.session.layout.name
        self._paint_banner()
        self._paint_motions()
        self._refresh()
        self.set_interval(1 / TICK_HZ, self._tick)
        self.focus()

    def _paint_banner(self) -> None:
        session = self.session
        text = Text()
        text.append(session.game.name, style="bold")
        text.append(f"  ·  {self.panel.name}", style="bold cyan")
        if self.panel.note:
            text.append(f"  {self.panel.note}", style="dim italic")
        text.append(f"\nMove {session.layout.movement_help()}   Attack {session.layout.attack_help()}", style="dim")
        self.query_one("#banner", Static).update(text)

    def _paint_motions(self) -> None:
        """Put the motion list into the player's notation, in columns as wide as the widest."""
        grid = self.query_one("#motions", ItemGrid)
        self._written = [self.notation.write_kind(kind) for kind in self.motions]
        grid.min_column_width = max(map(cell_len, self._written), default=0) + MOTION_GAP
        grid.refresh(layout=True)

    def _light_motions(self) -> None:
        """Write the motion list, lit as the panel lights what is held where a press now would bring one out."""
        live = {motion.kind for motion in self.session.trail if motion.outcome is Outcome.LIVE}
        labels = self.query_one("#motions", ItemGrid).query(Static)
        for label, kind, written in zip(labels, self.motions, self._written, strict=True):
            label.update(Text(written, style=LIT if kind in live else ""))

    def apply_panel(self, layout: ControlLayout, buttons: ButtonSet) -> None:
        """Take a rearranged panel, from the settings, without leaving it."""
        self.panel = buttons
        self.session.rebind(layout)
        if self.is_mounted:
            self._paint_banner()
            self._refresh()

    def apply_notation(self, notation: Notation) -> None:
        """Take the notation the motions are written in, before or during a session."""
        self.notation = notation
        if self.is_mounted:
            self._paint_motions()
            self._refresh()

    def apply_settings(self, game: Game, policy: BufferPolicy) -> None:
        """Take rules the player changed mid-session, from the settings modal."""
        self.session.retune(game, policy)
        if self.is_mounted:
            self._refresh()

    def on_key(self, event) -> None:  # ruff: ignore[missing-type-function-argument] - textual.events.Key
        """Feed every bound key to the session before Textual sees it."""
        if event.key not in self.session.layout.bindings:
            return
        event.stop()
        event.prevent_default()
        self.session.press(event.key)
        self._refresh()

    def handle_release(self, key: str) -> None:
        """Called by the app when the terminal reports a key going back up."""
        if key not in self.session.layout.bindings:
            return
        self.session.release(key)
        self._refresh()

    def on_app_blur(self) -> None:
        """Drop everything held when the terminal loses focus."""
        self.session.drop_holds()
        self._refresh()

    def _tick(self) -> None:
        if self.session.tick():
            self._refresh()

    def _refresh(self) -> None:
        session = self.session
        direction = session.direction
        self.query_one(DirectionGate).show(direction)
        self.query_one(ButtonPads).show(session.layout, session.held)
        brackets = trail_brackets(session.trail, self.notation)
        self.query_one(InputStrip).show(session.entries, direction, brackets, bracket_rows=MOTION_ROWS)
        self._light_motions()

        status = Text()
        status.append(f"{direction.glyph} {int(direction)} {direction.short}", style="bold")
        status.append(f"   {session.total_inputs} inputs")
        if session.gamepad_waiting:
            status.append("   no gamepad detected — plug one in", style="yellow")
        elif session.exact_input:
            status.append("   exact input tracking", style="dim green")
        else:
            status.append(f"   inferred holds, {session.hold_window_ms}ms window", style="dim")
        self.query_one("#status", Static).update(status)

    def action_reset(self) -> None:
        """Clear the history and go back to neutral."""
        self.session.reset()
        self._refresh()

    def action_back(self) -> None:
        """Return to the setup screen."""
        self.dismiss(None)
