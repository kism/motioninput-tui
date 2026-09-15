"""The trainer itself: press inputs, watch moves come out."""

from typing import TYPE_CHECKING, ClassVar, override

from rich.text import Text
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widgets import Footer, Static

from motioninput_tui.config import MOVELIST_MODES
from motioninput_tui.engine.notation import Direction
from motioninput_tui.engine.recognizer import BufferPolicy
from motioninput_tui.engine.session import TrainingSession, monotonic_ms
from motioninput_tui.notation_styles import DEFAULT as DEFAULT_NOTATION
from motioninput_tui.playback import FRAME_MS, Run, beats, plan
from motioninput_tui.terminal import detect
from motioninput_tui.tui.widgets.input_strip import MOTION_ROWS, InputStrip, trail_brackets
from motioninput_tui.tui.widgets.move_feed import MoveFeed, append_follow_up
from motioninput_tui.tui.widgets.movelist import MoveList, listed
from motioninput_tui.tui.widgets.panel import LIT_S, ButtonPads, DirectionGate, LivePanel
from motioninput_tui.tui.widgets.status_bar import StatusBar

from .base import SessionScreen

if TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual.timer import Timer

    from motioninput_tui.controls.layouts import ControlLayout
    from motioninput_tui.engine.recognizer import Activation, RecognisableMove
    from motioninput_tui.games.models import Character, Game, Move
    from motioninput_tui.notation_styles import Notation
    from motioninput_tui.playback import Timing

TICK_HZ = 60

LEAD_MS = 300
"""A moment of stillness before a playback starts, to get the eyes onto the stick."""

PICK_HINT = "ctrl+o to pick a move and play it back at its game's timing"
PICKING_HINT = "↑ ↓ pick a move, enter plays it back, ctrl+o or escape when done"

PICK_KEYS = frozenset({"up", "down", "enter", "escape"})
"""Picking's own while it is on, whatever the layout binds them to."""


class TrainingScreen(SessionScreen):
    """Reads raw key presses and renders what the engine made of them.

    The notation the move list and the feed are written in is set with
    :meth:`apply_notation`, before the screen is pushed and again whenever the
    player changes it, rather than being fixed at construction.
    """

    notation: Notation

    class MovelistChanged(Message):
        """ctrl+l stepped the move list on, for the app to remember for every game."""

        def __init__(self, mode: str) -> None:
            """Carry the view it is on now, one of ``MOVELIST_MODES``."""
            super().__init__()
            self.mode = mode

    BINDINGS: ClassVar = [
        # Priority, or Textual moves focus to the move list instead. Only shown
        # for a game with Super Arts; see check_action.
        Binding("tab", "next_super_art", "Super art", priority=True),
        Binding("ctrl+l", "cycle_movelist", "Move list"),
        # Picking a move to play back is the full-screen list's, and behind
        # ctrl+o, so the arrows and enter are free for any layout the rest of
        # the time. See check_action.
        Binding("ctrl+o", "pick", "Pick move"),
        Binding("enter", "play", "Play back"),
        Binding("up", "cursor(-1)", show=False),
        Binding("down", "cursor(1)", show=False),
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
    /* Under that, what a playback presses, or how to start one. */
    #playback { display: none; height: auto; padding: 0 1; }
    TrainingScreen.-movelist-full #mash, TrainingScreen.-movelist-full #playback { display: block; }
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
        """The view the move list is in. The app sets the player's last one
        before the screen is pushed, as it does the notation."""
        self.lit_move: RecognisableMove | None = None
        self.picking = False
        """Whether ctrl+o has the arrows and enter picking a move, full screen."""
        self.cursor: Move | None = None
        """The move picked for playback on the full-screen list."""
        self.playback: Run | None = None
        """The playback on the panel, until the player presses something."""
        self._playback_from = 0
        self._timings: dict[Move, Timing] = {}
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
        yield LivePanel(Static(id="mash"), Static(id="playback"))
        yield StatusBar(id="status")
        yield Footer()

    def on_mount(self) -> None:
        """Paint the static chrome and start the hold-expiry timer."""
        session = self.session
        self.title = f"{session.game.short_name} · {session.character.name}"
        self.sub_title = session.layout.name
        self._paint_banner()
        self._apply_movelist_mode()
        self._paint_movelist()
        self._paint_playback()
        self._refresh()
        self.set_interval(1 / TICK_HZ, self._tick)
        self.focus()

    @property
    def shown(self) -> TrainingSession:
        """The session on the panel: a playback's while one is showing, otherwise the player's."""
        return self.playback.session if self.playback is not None else self.session

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
        movelist = self.query_one(MoveList)
        movelist.cursor = self.cursor if self.picking else None
        movelist.show(session.character, self.notation, session.super_art, full=full, lit=self.lit_move)

    def _paint_playback(self) -> None:
        """What the playback on the panel presses, and when, or how to start one."""
        run = self.playback
        hint = PICKING_HINT if self.picking else PICK_HINT
        text = Text(hint, style="dim") if run is None else self._caption(run)
        self.query_one("#playback", Static).update(text)

    def _caption(self, run: Run) -> Text:
        """A playback written out as it goes, with the frames between each press.

        Then either how slow its steps may get before the game stops giving
        the move, which is how much room the player has, or what the trainer
        gives instead when no timing brings it out.
        """
        timing = run.timing
        text = Text()
        text.append(f"▶ {run.move.name}   ", style="bold")
        previous: int | None = None
        for at_ms, beat in beats(timing, run.session.layout):
            if previous is not None:
                frames = round((at_ms - previous) / FRAME_MS)
                text.append(f"  {frames}f  " if frames else " + ", style="dim")
            if isinstance(beat, Direction):
                text.append(self.notation.directions((beat,)), style="bold")
            else:
                text.append("+".join(button.value for button in beat), style="bold yellow")
            previous = at_ms
        if not timing.works:
            instead = ", ".join(timing.instead) or "nothing"
            text.append(f"   the trainer gives {instead} for these inputs", style="red")
        elif timing.slowest_ms is not None:
            text.append(f"   steps up to {round(timing.slowest_ms / FRAME_MS)}f apart still land", style="dim")
        return text

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
        inputs = self.session.total_inputs
        changed = self.session.tick()
        if self.session.total_inputs != inputs:  # a pad, which comes in here rather than through on_key
            self._hand_back()
        if self.playback is not None:
            changed |= self.playback.advance(monotonic_ms() - self._playback_from)
        if changed:
            self._refresh()

    def _paint_mash(self) -> None:
        """The newest move's follow-through, if it wants taps or a mash, for when the feed is hidden."""
        session = self.shown
        mash = Text()
        latest = session.activations[0] if session.activations else None
        if latest is not None and latest.follow_up is not None:
            mash.append(f"{latest.name}  ", style="bold")
            append_follow_up(mash, latest.follow_up, newest=True)
        self.query_one("#mash", Static).update(mash)

    def on_key(self, event) -> None:  # ruff: ignore[missing-type-function-argument] - textual.events.Key
        """Feed every key press to the session before Textual sees it, bar picking's own while it is on."""
        if self.picking and event.key in PICK_KEYS:
            return
        if event.key in self.session.layout.bindings:
            event.stop()
            event.prevent_default()
            self._hand_back()
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
        # The panel and the history are a playback's while one is showing; the
        # feed and the status are always the player's.
        shown = self.shown
        # The motions the stick has made laid over the inputs that made them,
        # as the input display does.
        brackets = trail_brackets(shown.trail, self.notation)
        self.query_one("#strip", InputStrip).show(shown.entries, shown.direction, brackets, bracket_rows=MOTION_ROWS)
        self._paint_mash()
        self.query_one(MoveFeed).show(self.session.activations, self.notation)
        self.query_one(DirectionGate).show(shown.direction, self.notation)
        self.query_one(ButtonPads).show(shown.layout, shown.held)
        latest = shown.activations[0] if shown.activations else None
        if latest is not self._latest:
            self._latest = latest
            self._light(latest.move if latest is not None else None)

        self.query_one(StatusBar).show(self.session)

    def apply_notation(self, notation: Notation) -> None:
        """Take the notation moves are written in, before or during a session."""
        self.notation = notation
        if self.is_mounted:
            self._paint_movelist()
            self._paint_playback()
            self._refresh()

    def apply_settings(self, policy: BufferPolicy) -> None:
        """Take a buffer policy the player changed mid-session, from the settings modal."""
        self.session.retune(policy)
        self._refresh()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        """Only offer the Super Art key for a game that has them, and picking on the full-screen list."""
        del parameters
        if action == "pick":
            return self.movelist_mode == "full"
        if action in {"play", "cursor"}:
            return self.picking
        if action == "next_super_art":
            return True if self.session.super_arts else None
        return True

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
        self._stop_playback()
        self.session.reset()
        self._refresh()

    def action_cycle_movelist(self) -> None:
        """Step the move list on: beside the trainer, hidden, the whole screen.

        Full screen hides the activation feed, so the newest move's
        follow-through is prompted under the history instead, and ctrl+o
        picks a move there to play back. The live panel and the status stay
        along the bottom whichever it is.
        """
        self.movelist_mode = MOVELIST_MODES[(MOVELIST_MODES.index(self.movelist_mode) + 1) % len(MOVELIST_MODES)]
        self._apply_movelist_mode()
        self.post_message(self.MovelistChanged(self.movelist_mode))
        self.picking = False
        self._stop_playback()
        self.refresh_bindings()
        self._paint_movelist()
        self._paint_playback()

    def _apply_movelist_mode(self) -> None:
        """Lay the screen out for the move list's view; the CSS does the rest."""
        self.set_class(self.movelist_mode == "full", "-movelist-full")
        self.set_class(self.movelist_mode == "hidden", "-movelist-hidden")

    def action_pick(self) -> None:
        """Start or stop picking a move to play back, which takes the arrows and enter while it lasts."""
        self.picking = not self.picking
        if self.picking and self.cursor is None:
            self.cursor = next(iter(self._playable()), None)
        self.refresh_bindings()
        self._paint_movelist()
        self._paint_playback()

    @override
    def action_back(self) -> None:
        """Stop picking if picking, otherwise go back to the setup screen."""
        if self.picking:
            self.action_pick()
            return
        super().action_back()

    def _playable(self) -> list[Move]:
        """The moves a playback can be made of, in the list's order: the trainable ones."""
        return [move for move in listed(self.session.character) if move.trainable]

    def action_cursor(self, step: int) -> None:
        """Pick the move ``step`` rows on for playback, stopping at either end."""
        moves = self._playable()
        if not moves:
            return
        index = moves.index(self.cursor) + step if self.cursor in moves else 0
        self.cursor = moves[max(0, min(index, len(moves) - 1))]
        self._paint_movelist()

    def action_play(self) -> None:
        """Play the picked move back on the panel, at the timing that gives most room in this game.

        It runs through a session of its own, so the player's history is back
        where they left it the moment they press something.
        """
        move = self.cursor
        if move is None:
            return
        session = self.session
        if move not in self._timings:  # finding it plays the move a dozen times over
            self._timings[move] = plan(session.game, session.character, session.layout, move)
        self.playback = Run(session.game, session.character, session.layout, move, self._timings[move])
        self._playback_from = monotonic_ms() + LEAD_MS
        self._paint_playback()
        self._refresh()

    def _hand_back(self) -> None:
        """The player pressed something: the panel is theirs again, and picking stops.

        The cursor stays where it was, unmarked, for ctrl+o to pick up from.
        """
        self._stop_playback()
        if self.picking:
            self.action_pick()

    def _stop_playback(self) -> None:
        """Hand the panel back to the player, without lighting their last move again."""
        if self.playback is None:
            return
        self.playback = None
        self._latest = self.session.activations[0] if self.session.activations else None
        self._paint_playback()
        self._refresh()
