"""The input display: the game's panel, and every motion the game has.

It is the first character of every roster, and runs on the same
:class:`~motioninput_tui.engine.session.TrainingSession` as the trainer, so
directions are cleaned and holds inferred exactly as they are when a move is on
the line. Its moves are every motion in the game on any button (see
:mod:`motioninput_tui.games.loader`), so what the stick makes is drawn over the
history whoever's move it would be.
"""

from typing import TYPE_CHECKING, ClassVar, NamedTuple, override

from rich.cells import cell_len
from rich.table import Table
from rich.text import Text
from textual.binding import Binding
from textual.containers import Center, Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Static

from motioninput_tui.engine.motions import MotionKind
from motioninput_tui.engine.recognizer import BufferPolicy
from motioninput_tui.engine.session import Outcome, TrainingSession
from motioninput_tui.games.loader import INPUT_DISPLAY
from motioninput_tui.notation_styles import DEFAULT as DEFAULT_NOTATION
from motioninput_tui.notation_styles import MOTION_NAMES, MOTION_SHORTHANDS
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

NAME_GAP = 3
"""Cells between a motion and its name: wider than the gap inside a compound motion."""

MOTIONS_FRAME = 5
"""What the motion pane adds around its list: a border and a cell of padding
each side, and a one-cell scrollbar for a list taller than the pane."""


class Writing(NamedTuple):
    """One way ctrl+l writes the motion list."""

    title: str
    spelled_out: bool
    """Directions spelled out, rather than in the player's notation."""
    names: dict[MotionKind, str]


WRITINGS = (
    Writing("Motions", spelled_out=False, names=MOTION_NAMES),
    Writing("Motions, spelled out", spelled_out=True, names=MOTION_NAMES),
    Writing("Motions, shorthand", spelled_out=False, names=MOTION_SHORTHANDS),
    Writing("Motions, spelled out, shorthand", spelled_out=True, names=MOTION_SHORTHANDS),
)
"""What ctrl+l steps through, starting from the first."""


class InputDisplayScreen(Screen):
    """Draws the panel live beside the game's motions, over the input history."""

    notation: Notation

    BINDINGS: ClassVar = [
        Binding("escape", "back", "Change character"),
        Binding("ctrl+r", "reset", "Reset"),
        Binding("ctrl+b", "app.settings", "Settings"),
        Binding("ctrl+n", "app.notation", "Notation"),
        Binding("ctrl+l", "cycle_writing", "Writing"),
        # Nothing here takes text input, so drop Screen's copy/paste bindings
        # from the key panel; ctrl+c stays as the quit shortcut.
        Binding("ctrl+c", "app.help_quit", show=False, system=True),
    ]

    DEFAULT_CSS = """
    InputDisplayScreen { layout: vertical; }
    InputDisplayScreen #banner { height: auto; padding: 0 1; background: $panel; }
    InputDisplayScreen #body { height: 1fr; }
    /* The panel keeps the width it needs, and the motions take at most 40%,
       which leaves it that from 80 columns up; past that, names wrap. */
    InputDisplayScreen #panel-area { width: 1fr; min-width: 48; height: 1fr; align: center middle; }
    InputDisplayScreen #panel { width: auto; height: auto; }
    InputDisplayScreen #motions {
        max-width: 40%;
        height: 1fr;
        border: round $panel;
        padding: 0 1;
        scrollbar-size-vertical: 1;
    }
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
        self.writing = WRITINGS[0]
        order = list(MotionKind)
        self.motions = sorted({move.motion.kind for move in display.moves if move.motion is not None}, key=order.index)
        """Every motion the game has, once each, in the order the engine lists them."""

    @override
    def compose(self) -> ComposeResult:
        """The gate and the buttons beside the game's motions, over the input history."""
        yield Static(id="banner")
        with Horizontal(id="body"):
            with Center(id="panel-area"), Horizontal(id="panel"):
                yield DirectionGate()
                yield ButtonPads()
            with VerticalScroll(id="motions") as motions:
                motions.border_title = self.writing.title
                yield Static(id="motion-list")
        # Outside the panes, so the history has the whole width to fill.
        yield InputStrip(id="strip")
        yield Static(id="status")
        yield Footer()

    def on_mount(self) -> None:
        """Paint the chrome and start the tick that expires holds."""
        self.title = f"{self.session.game.short_name} · Input display"
        self.sub_title = self.session.layout.name
        self._paint_banner()
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
        """Every motion and its name, lit as the panel lights what is held where a press now would bring it out.

        A table, so that in a narrow pane a long name wraps under itself rather than being cut off.
        """
        live = {motion.kind for motion in self.session.trail if motion.outcome is Outcome.LIVE}
        written = [self.written_in.write_kind(kind) for kind in self.motions]
        names = [self.writing.names[kind] for kind in self.motions]
        # Sized here rather than left to auto: rich measures a table to the width
        # it is offered, which in a pane sized to its content is nothing.
        unwrapped = max(map(cell_len, written), default=0) + NAME_GAP + max(map(cell_len, names), default=0)
        self.query_one("#motions", VerticalScroll).styles.width = unwrapped + MOTIONS_FRAME
        table = Table.grid(padding=(0, NAME_GAP))
        table.add_column(no_wrap=True)
        table.add_column()
        for kind, text, name in zip(self.motions, written, names, strict=True):
            table.add_row(text, name, style=LIT if kind in live else None)
        self.query_one("#motion-list", Static).update(table)

    def apply_panel(self, layout: ControlLayout, buttons: ButtonSet) -> None:
        """Take a rearranged panel, from the settings, without leaving it."""
        self.panel = buttons
        self.session.rebind(layout)
        if self.is_mounted:
            self._paint_banner()
            self._refresh()

    @property
    def written_in(self) -> Notation:
        """The notation the motions are written in: the player's, or spelled out, as ctrl+l has it."""
        return self.notation.spelled_out() if self.writing.spelled_out else self.notation

    def action_cycle_writing(self) -> None:
        """Step the motions on: the player's notation, spelled out, then both again with shorthand names."""
        self.writing = WRITINGS[(WRITINGS.index(self.writing) + 1) % len(WRITINGS)]
        self.query_one("#motions", VerticalScroll).border_title = self.writing.title
        self._refresh()

    def apply_notation(self, notation: Notation) -> None:
        """Take the notation the motions are written in, before or during a session."""
        self.notation = notation
        if self.is_mounted:
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
        brackets = trail_brackets(session.trail, self.written_in)
        self.query_one(InputStrip).show(session.entries, direction, brackets, bracket_rows=MOTION_ROWS)
        self._paint_motions()

        status = Text()
        if session.gamepad_waiting:
            status.append("   no gamepad detected — plug one in", style="yellow")
        elif session.exact_input:
            pass
        else:
            status.append(f"   inferred holds, {session.hold_window_ms}ms window", style="yellow")
        self.query_one("#status", Static).update(status)

    def action_reset(self) -> None:
        """Clear the history and go back to neutral."""
        self.session.reset()
        self._refresh()

    def action_back(self) -> None:
        """Return to the setup screen."""
        self.dismiss(None)
