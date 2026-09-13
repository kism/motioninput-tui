"""The trainer itself: press inputs, watch moves come out."""

from typing import TYPE_CHECKING, ClassVar

from rich.text import Text
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Static

from motioninput_tui.engine.recognizer import BufferPolicy
from motioninput_tui.engine.session import TrainingSession
from motioninput_tui.notation_styles import DEFAULT as DEFAULT_NOTATION
from motioninput_tui.terminal import detect
from motioninput_tui.tui.widgets.input_strip import MOTION_ROWS, InputStrip, trail_brackets
from motioninput_tui.tui.widgets.move_feed import MoveFeed, append_follow_up
from motioninput_tui.tui.widgets.movelist import MoveList
from motioninput_tui.tui.widgets.panel import LIT_S, ButtonPads, DirectionGate, LivePanel
from motioninput_tui.tui.widgets.status_bar import StatusBar

from .base import SessionScreen

if TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual.timer import Timer

    from motioninput_tui.controls.layouts import ControlLayout
    from motioninput_tui.engine.recognizer import Activation, RecognisableMove
    from motioninput_tui.games.models import Character, Game
    from motioninput_tui.notation_styles import Notation

TICK_HZ = 60

MOVELIST_MODES = ("beside", "full", "hidden")
"""What ctrl+l steps through, starting from the first."""


class TrainingScreen(SessionScreen):
    """Reads raw key presses and renders what the engine made of them.

    The notation the move list and the feed are written in is set with
    :meth:`apply_notation`, before the screen is pushed and again whenever the
    player changes it, rather than being fixed at construction.
    """

    notation: Notation

    BINDINGS: ClassVar = [
        # Priority, or Textual moves focus to the move list instead. Only shown
        # for a game with Super Arts; see check_action.
        Binding("tab", "next_super_art", "Super art", priority=True),
        Binding("ctrl+l", "cycle_movelist", "Move list"),
    ]

    DEFAULT_CSS = """
    TrainingScreen { layout: vertical; }
    #banner { height: auto; padding: 0 1; background: $panel; }
    #warning { height: auto; padding: 0 1; color: $warning; }
    #body { height: 1fr; }
    #left { width: 1fr; }
    #feed-title { padding: 0 1; text-style: bold; }
    /* Under the history, for when a full-screen move list hides the feed. */
    #mash { display: none; height: 1; padding: 0 2 0 1; text-align: right; }
    TrainingScreen.-movelist-full #mash { display: block; }
    TrainingScreen.-movelist-full #left { display: none; }
    TrainingScreen.-movelist-full #movelist { width: 1fr; border-left: none; }
    TrainingScreen.-movelist-hidden #movelist { display: none; }
    """

    def __init__(
        self,
        game: Game,
        character: Character,
        layout: ControlLayout,
        *,
        exact_input: bool = False,
        policy: BufferPolicy = BufferPolicy.CONSUME,
    ) -> None:
        """Start a session for this game, character and layout."""
        super().__init__()
        self.session = TrainingSession(game, character, layout, exact_input=exact_input, policy=policy)
        self.terminal = detect()
        self.notation = DEFAULT_NOTATION
        self.movelist_mode = MOVELIST_MODES[0]
        self.lit_move: RecognisableMove | None = None
        self._latest: Activation | None = None
        self._unlight: Timer | None = None

    def compose(self) -> ComposeResult:
        """The feed beside the move list, over the input history and the status, as the input display lays out."""
        yield Static(id="banner")
        if self.terminal.should_warn:
            yield Static(Text(f"⚠ {self.terminal.warning()}"), id="warning")
        with Horizontal(id="body"):
            with Vertical(id="left"):
                yield Static("Activated moves", id="feed-title")
                yield MoveFeed(id="feed")
            yield MoveList(id="movelist")
        # The stick and the buttons with the history beside them, as on the
        # input display, and under the history the newest move's follow-through.
        yield LivePanel(Static(id="mash"))
        yield StatusBar(id="status")
        yield Footer()

    def on_mount(self) -> None:
        """Paint the static chrome and start the hold-expiry timer."""
        session = self.session
        self.title = f"{session.game.short_name} · {session.character.name}"
        self.sub_title = session.layout.name
        self._paint_banner()
        self._paint_movelist()
        self._refresh()
        self.set_interval(1 / TICK_HZ, self._tick)
        self.focus()

    def _paint_banner(self) -> None:
        session = self.session
        text = Text()
        text.append(f"{session.game.name}", style="bold")
        text.append(f"  ·  {session.character.name}", style="bold cyan")
        if session.character.title:
            text.append(f" ({session.character.title})", style="dim")
        if session.super_art:
            text.append(f"  ·  Super Art {session.super_art}", style="bold magenta")
            text.append("  tab to change", style="dim")
        # The game's notes are not here: they head the settings menu, ctrl+b.
        text.append(f"\nMove {session.layout.movement_help()}   Attack {session.layout.attack_help()}", style="dim")
        self.query_one("#banner", Static).update(text)

    def _paint_movelist(self) -> None:
        session = self.session
        full = self.movelist_mode == "full"
        self.query_one(MoveList).show(session.character, self.notation, session.super_art, full=full, lit=self.lit_move)

    def _light(self, move: RecognisableMove | None) -> None:
        """Light ``move`` in the move list, and put it out again after ``LIT_S``.

        A move coming out while another is lit takes over, with a fresh timer,
        so a stale one can never put the new move out early.
        """
        if self._unlight is not None:
            self._unlight.stop()
        self.lit_move = move
        self._paint_movelist()
        if move is not None:
            self._unlight = self.set_timer(LIT_S, lambda: self._light(None))

    def on_resize(self) -> None:
        """Resize the move list with the screen, since beside the trainer it may take up to half."""
        self._paint_movelist()

    def _tick(self) -> None:
        if self.session.tick():
            self._refresh()

    def _paint_mash(self) -> None:
        """The newest move's follow-through, if it wants taps or a mash, for when the feed is hidden."""
        session = self.session
        mash = Text()
        latest = session.activations[0] if session.activations else None
        if latest is not None and latest.follow_up is not None:
            mash.append(f"{latest.name}  ", style="bold")
            append_follow_up(mash, latest.follow_up, newest=True)
        self.query_one("#mash", Static).update(mash)

    def on_key(self, event) -> None:  # ruff: ignore[missing-type-function-argument] - textual.events.Key
        """Feed every key press to the session before Textual sees it."""
        if event.key in self.session.layout.bindings:
            event.stop()
            event.prevent_default()
            if self.session.press(event.key):
                self._refresh()

    def handle_release(self, key: str) -> None:
        """Called by the app when the terminal reports a key going back up."""
        if key in self.session.layout.bindings and self.session.release(key):
            self._refresh()

    def on_app_blur(self) -> None:
        """Drop every hold when the terminal loses focus.

        Keyboard releases that happen while unfocused never arrive, so anything
        still held would otherwise stick. A gamepad is unaffected by focus, so
        it just re-asserts whatever it is holding on the next poll.
        """
        self.session.drop_holds()
        self._refresh()

    def _refresh(self) -> None:
        session = self.session
        # The motions the stick has made laid over the inputs that made them,
        # as the input display does.
        brackets = trail_brackets(session.trail, self.notation)
        self.query_one("#strip", InputStrip).show(
            session.entries, session.direction, brackets, bracket_rows=MOTION_ROWS
        )
        self._paint_mash()
        self.query_one(MoveFeed).show(session.activations, self.notation)
        self.query_one(DirectionGate).show(session.direction, self.notation)
        self.query_one(ButtonPads).show(session.layout, session.held)
        latest = session.activations[0] if session.activations else None
        if latest is not self._latest:
            self._latest = latest
            self._light(latest.move if latest is not None else None)

        self.query_one(StatusBar).show(session)

    def apply_notation(self, notation: Notation) -> None:
        """Take the notation moves are written in, before or during a session."""
        self.notation = notation
        if self.is_mounted:
            self._paint_movelist()
            self._refresh()

    def apply_settings(self, policy: BufferPolicy) -> None:
        """Take a buffer policy the player changed mid-session, from the settings modal."""
        self.session.retune(policy)
        self._refresh()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        """Only offer the Super Art key for a game that has them, so only SF3."""
        del parameters
        if action != "next_super_art":
            return True
        return True if self.session.super_arts else None

    def action_next_super_art(self) -> None:
        """Equip the next Super Art, wrapping round.

        Only one is live at a time, exactly as in the game, which is what lets
        the recogniser tell three supers on the same ``qcf,qcf + P`` apart.
        """
        arts = self.session.super_arts
        if not arts:
            return
        self.session.select_super_art(arts[(arts.index(self.session.super_art) + 1) % len(arts)])
        self._paint_banner()
        self._paint_movelist()
        self._refresh()

    def action_reset(self) -> None:
        """Clear the input buffer and the feed."""
        self.session.reset()
        self._refresh()

    def action_cycle_movelist(self) -> None:
        """Step the move list on: beside the trainer, the whole screen, hidden.

        Full screen hides the activation feed, so the newest move's
        follow-through is prompted under the history instead. The live panel
        and the status stay along the bottom whichever it is.
        """
        self.movelist_mode = MOVELIST_MODES[(MOVELIST_MODES.index(self.movelist_mode) + 1) % len(MOVELIST_MODES)]
        self.set_class(self.movelist_mode == "full", "-movelist-full")
        self.set_class(self.movelist_mode == "hidden", "-movelist-hidden")
        self._paint_movelist()
