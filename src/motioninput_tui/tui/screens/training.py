"""The trainer itself: press inputs, watch moves come out."""

from typing import TYPE_CHECKING, ClassVar

from rich.text import Text
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Static

from motioninput_tui.engine.recognizer import BufferPolicy
from motioninput_tui.engine.session import TrainingSession
from motioninput_tui.notation_styles import DEFAULT as DEFAULT_NOTATION
from motioninput_tui.terminal import detect
from motioninput_tui.tui.widgets.input_strip import InputStrip, trail_brackets
from motioninput_tui.tui.widgets.move_feed import MoveFeed, append_follow_up
from motioninput_tui.tui.widgets.movelist import MoveList
from motioninput_tui.tui.widgets.panel import ButtonPads, DirectionGate

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

LIT_S = 0.5
"""How long the last move to come out stays lit in the move list, in seconds."""

BRACKET_ROWS = 7
"""Lines of motions over the full-screen panel's history: the stick's nine rows,
less the inputs and the one under them."""


class TrainingScreen(Screen):
    """Reads raw key presses and renders what the engine made of them.

    The notation the move list and the feed are written in is set with
    :meth:`apply_notation`, before the screen is pushed and again whenever the
    player changes it, rather than being fixed at construction.
    """

    notation: Notation

    BINDINGS: ClassVar = [
        Binding("escape", "back", "Change character"),
        # Priority, or Textual moves focus to the move list instead. Only shown
        # for a game with Super Arts; see check_action.
        Binding("tab", "next_super_art", "Super art", priority=True),
        Binding("ctrl+r", "reset", "Reset buffer"),
        Binding("ctrl+l", "cycle_movelist", "Move list"),
        Binding("ctrl+b", "app.settings", "Settings"),
        Binding("ctrl+n", "app.notation", "Notation"),
        # Nothing here takes text input, so drop Screen's copy/paste bindings
        # from the key panel; ctrl+c stays as the quit shortcut.
        Binding("ctrl+c", "app.help_quit", show=False, system=True),
    ]

    DEFAULT_CSS = """
    TrainingScreen { layout: vertical; }
    #banner { height: auto; padding: 0 1; background: $panel; }
    #warning { height: auto; padding: 0 1; color: $warning; }
    #body { height: 1fr; }
    #left { width: 1fr; }
    #feed-title { padding: 0 1; text-style: bold; }
    #status { height: auto; padding: 0 1; color: $text-muted; border-top: solid $panel; }
    #pads { height: auto; display: none; border-top: solid $panel; }
    /* As tall as the stick, three rows of three-line boxes, with the inputs
       level with its bottom row, the motions stacked over them and a mash
       prompt under them. */
    #history { width: 1fr; height: 9; align-vertical: bottom; }
    #history InputStrip { height: auto; padding: 0 1; border-bottom: none; }
    #mash { height: 1; padding: 0 2 0 1; text-align: right; }
    TrainingScreen.-movelist-full #pads { display: block; }
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
        """Start a session for this game, character and layout.

        The game's rules arrive already tuned to the player's settings; see
        :func:`motioninput_tui.settings.tuned_game`.
        """
        super().__init__()
        self.session = TrainingSession(game, character, layout, exact_input=exact_input, policy=policy)
        self.terminal = detect()
        self.notation = DEFAULT_NOTATION
        self.movelist_mode = MOVELIST_MODES[0]
        self.lit_move: RecognisableMove | None = None
        self._latest: Activation | None = None
        self._unlight: Timer | None = None

    def compose(self) -> ComposeResult:
        """Banner, input strip, activation feed and the move list."""
        yield Static(id="banner")
        if self.terminal.should_warn:
            yield Static(Text(f"⚠ {self.terminal.warning()}"), id="warning")
        with Horizontal(id="body"):
            with Vertical(id="left"):
                yield InputStrip(id="strip")
                yield Static("Activated moves", id="feed-title")
                yield MoveFeed(id="feed")
                yield Static(id="status")
            yield MoveList(id="movelist")
        # The live panel and its own input history, under a full-screen move
        # list that hides the left pane, with the motions the stick has made.
        with Horizontal(id="pads"):
            yield DirectionGate()
            yield ButtonPads()
            with Vertical(id="history"):
                yield InputStrip(id="panel-strip")
                yield Static(id="mash")
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
        text.append(f"\nMove {session.layout.movement_help()}   Attack {session.layout.attack_help()}\n", style="dim")
        for note in session.game.notes:
            text.append(f"• {note}\n", style="italic dim")
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

    def _tick(self) -> None:
        if self.session.tick():
            self._refresh()

    def _paint_history(self) -> None:
        """The full-screen panel's input history, with the trail of motions laid over the inputs that made them.

        Newest nearest the inputs. One a press would have beaten is struck, and
        a finished one is green if a move came out on it, dim if not. Under
        them, the newest move's follow-through, if it wants taps or a mash.
        """
        if self.movelist_mode != "full":
            return
        session = self.session
        brackets = trail_brackets(session.trail, self.notation)
        strip = self.query_one("#panel-strip", InputStrip)
        strip.show(session.entries, session.direction, brackets, bracket_rows=BRACKET_ROWS)
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
        self.query_one("#strip", InputStrip).show(session.entries, session.direction)
        self._paint_history()
        self.query_one(MoveFeed).show(session.activations, self.notation)
        self.query_one(DirectionGate).show(session.direction)
        self.query_one(ButtonPads).show(session.layout, session.held)
        latest = session.activations[0] if session.activations else None
        if latest is not self._latest:
            self._latest = latest
            self._light(latest.move if latest is not None else None)

        status = Text()
        plural = "" if session.total_activations == 1 else "s"
        status.append(f"{session.total_activations} move{plural} from {session.total_inputs} inputs")
        if session.gamepad_waiting:
            status.append("   no gamepad detected — plug one in", style="yellow")
        elif session.exact_input:
            pass
        else:
            status.append(f"   inferred holds, {session.hold_window_ms}ms window", style="dim")
        if session.policy is BufferPolicy.LOOSE:
            status.append("   loose buffer: inputs are reused between moves", style="yellow")
        if not session.ruleset.lenient_half_circles:
            status.append("   strict half circles", style="yellow")
        advice = session.keyboard_advice
        if advice:
            status.append(f"\n⚠ {advice}", style="yellow")
        self.query_one("#status", Static).update(status)

    def apply_notation(self, notation: Notation) -> None:
        """Take the notation moves are written in, before or during a session."""
        self.notation = notation
        if self.is_mounted:
            self._paint_movelist()
            self._refresh()

    def apply_settings(self, game: Game, policy: BufferPolicy) -> None:
        """Take rules the player changed mid-session, from the settings modal."""
        self.session.retune(game, policy)
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

        Full screen swaps the input strip for the live button panel, so what
        is pressed stays visible while the list is being read.
        """
        self.movelist_mode = MOVELIST_MODES[(MOVELIST_MODES.index(self.movelist_mode) + 1) % len(MOVELIST_MODES)]
        self.set_class(self.movelist_mode == "full", "-movelist-full")
        self.set_class(self.movelist_mode == "hidden", "-movelist-hidden")
        self._paint_movelist()
        # A strip trims its history to its width, which is nothing while hidden.
        self.call_after_refresh(self._refresh)

    def action_back(self) -> None:
        """Return to the setup screen."""
        self.dismiss(None)
