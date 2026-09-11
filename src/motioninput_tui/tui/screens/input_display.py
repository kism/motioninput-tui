"""The input display: the game's panel, and every motion the game has.

It is the first character of every roster, and runs on the same
:class:`~motioninput_tui.engine.session.TrainingSession` as the trainer, so
directions are cleaned and holds inferred exactly as they are when a move is on
the line. Its moves are every motion in the game on any button (see
:mod:`motioninput_tui.games.loader`), so what the stick makes is drawn over the
history whoever's move it would be.
"""

from typing import TYPE_CHECKING, ClassVar, NamedTuple, override

from rich.table import Table
from rich.text import Text
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Static

from motioninput_tui.engine.motions import MotionKind
from motioninput_tui.engine.recognizer import BufferPolicy
from motioninput_tui.engine.session import Outcome, TrainingSession
from motioninput_tui.games.loader import INPUT_DISPLAY
from motioninput_tui.notation_styles import DEFAULT as DEFAULT_NOTATION
from motioninput_tui.notation_styles import MOTION_NAMES, MOTION_SHORTHANDS
from motioninput_tui.tui.widgets.input_strip import MOTION_ROWS, InputStrip, trail_brackets
from motioninput_tui.tui.widgets.panel import LIT, LIT_S, ButtonPads, DirectionGate, LivePanel
from motioninput_tui.tui.widgets.status_bar import StatusBar

if TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual.timer import Timer

    from motioninput_tui.controls.buttons import ButtonSet
    from motioninput_tui.controls.layouts import ControlLayout
    from motioninput_tui.engine.recognizer import Activation
    from motioninput_tui.games.models import Game
    from motioninput_tui.notation_styles import Notation

TICK_HZ = 60

NAME_GAP = 3
"""Cells between a motion and its name: wider than the gap inside a compound motion."""

LIVE = "black on dark_sea_green"
"""A motion a press would still bring out: paler than ``LIT``, which is kept for one that came out."""


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
    """The game's motions over the live panel: the stick, the buttons and the history beside them."""

    notation: Notation

    BINDINGS: ClassVar = [
        Binding("escape", "back", "Change character"),
        Binding("ctrl+r", "reset", "Reset"),
        Binding("ctrl+b", "app.settings", "Settings"),
        Binding("ctrl+n", "app.notation", "Notation"),
        Binding("ctrl+l", "cycle_writing", "Writing"),
        Binding("ctrl+p", "toggle_panel", "Live input"),
        # Nothing here takes text input, so drop Screen's copy/paste bindings
        # from the key panel; ctrl+c stays as the quit shortcut.
        Binding("ctrl+c", "app.help_quit", show=False, system=True),
    ]

    DEFAULT_CSS = """
    InputDisplayScreen { layout: vertical; }
    InputDisplayScreen #banner { height: auto; padding: 0 1; background: $panel; }
    InputDisplayScreen #motions {
        height: 1fr;
        border: round $panel;
        padding: 0 1;
        scrollbar-size-vertical: 1;
    }
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
        self.lit_kind: MotionKind | None = None
        self._latest: Activation | None = None
        self._unlight: Timer | None = None
        order = list(MotionKind)
        self.motions = sorted({move.motion.kind for move in display.moves if move.motion is not None}, key=order.index)
        """Every motion the game has, once each, in the order the engine lists them."""

    @override
    def compose(self) -> ComposeResult:
        """The game's motions over the live panel and the status, as the trainer lays out."""
        yield Static(id="banner")
        with VerticalScroll(id="motions") as motions:
            motions.border_title = self.writing.title
            yield Static(id="motion-list")
        yield LivePanel()
        yield StatusBar(id="status")
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
        """Every motion and its name: pale while a press would bring it out, lit a moment once one has.

        A table, so that in a narrow pane a long name wraps under itself rather than being cut off.
        """
        live = {motion.kind for motion in self.session.trail if motion.outcome is Outcome.LIVE}
        written = [self.written_in.write_kind(kind) for kind in self.motions]
        names = [self.writing.names[kind] for kind in self.motions]
        table = Table.grid(padding=(0, NAME_GAP))
        table.add_column(no_wrap=True)
        table.add_column()
        for kind, text, name in zip(self.motions, written, names, strict=True):
            style = LIT if kind is self.lit_kind else LIVE if kind in live else None
            table.add_row(text, name, style=style)
        self.query_one("#motion-list", Static).update(table)

    def _light(self, kind: MotionKind | None) -> None:
        """Light the motion a move just came out on, as the trainer lights the move, and put it out after ``LIT_S``.

        A fresh one takes over with a fresh timer, so a stale timer never puts it out early.
        """
        if self._unlight is not None:
            self._unlight.stop()
        self.lit_kind = kind
        if kind is not None:
            self._unlight = self.set_timer(LIT_S, lambda: self._light(None))
        self._paint_motions()

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
        self.query_one(DirectionGate).show(direction, self.notation)
        self.query_one(ButtonPads).show(session.layout, session.held)
        brackets = trail_brackets(session.trail, self.written_in)
        self.query_one(InputStrip).show(session.entries, direction, brackets, bracket_rows=MOTION_ROWS)
        latest = session.activations[0] if session.activations else None
        if latest is not self._latest:
            self._latest = latest
            motion = latest.move.motion if latest is not None else None
            self._light(motion.kind if motion is not None else None)
        self._paint_motions()
        self.query_one(StatusBar).show(session)

    def action_reset(self) -> None:
        """Clear the history and go back to neutral."""
        self.session.reset()
        self._refresh()

    def action_toggle_panel(self) -> None:
        """Show or hide the stick and the buttons beside the history."""
        self.query_one(LivePanel).toggle()

    def action_back(self) -> None:
        """Return to the setup screen."""
        self.dismiss(None)
