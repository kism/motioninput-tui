"""The trainer itself: press inputs, watch moves come out."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from rich.text import Text
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Footer, Static

from motioninput_tui.engine.recognizer import BufferPolicy
from motioninput_tui.engine.session import TrainingSession
from motioninput_tui.terminal import detect
from motioninput_tui.tui.widgets.input_strip import InputStrip
from motioninput_tui.tui.widgets.move_feed import MoveFeed
from motioninput_tui.tui.widgets.movelist import MoveList

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from motioninput_tui.controls.layouts import ControlLayout
    from motioninput_tui.games.models import Character, Game

TICK_HZ = 60


class TrainingScreen(Screen):
    """Reads raw key presses and renders what the engine made of them."""

    BINDINGS: ClassVar = [
        Binding("escape", "back", "Change character"),
        Binding("ctrl+r", "reset", "Reset buffer"),
        Binding("ctrl+l", "toggle_movelist", "Move list"),
        Binding("ctrl+b", "toggle_policy", "Buffer rule"),
        Binding("ctrl+c", "quit", "Quit"),
    ]

    class PolicyChanged(Message):
        """Posted when the player toggles the buffer rule, so it can be saved."""

        def __init__(self, policy: BufferPolicy) -> None:
            """Carry the policy now in force."""
            super().__init__()
            self.policy = policy

    DEFAULT_CSS = """
    TrainingScreen { layout: vertical; }
    #banner { height: auto; padding: 0 1; background: $panel; }
    #warning { height: auto; padding: 0 1; color: $warning; }
    #body { height: 1fr; }
    #left { width: 1fr; }
    #feed-title { padding: 0 1; text-style: bold; }
    #status { height: auto; padding: 0 1; color: $text-muted; border-top: solid $panel; }
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
        yield Footer()

    def on_mount(self) -> None:
        """Paint the static chrome and start the hold-expiry timer."""
        session = self.session
        self.title = f"{session.game.short_name} · {session.character.name}"
        self.sub_title = session.layout.name
        self._paint_banner()
        self.query_one(MoveList).show(session.character)
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
        text.append(f"\nMove {session.layout.movement_help()}   Attack {session.layout.attack_help()}\n", style="dim")
        for note in session.game.notes:
            text.append(f"• {note}\n", style="italic dim")
        self.query_one("#banner", Static).update(text)

    def _tick(self) -> None:
        if self.session.tick():
            self._refresh()

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

        Releases that happen while unfocused never arrive, so anything still
        held would otherwise stick.
        """
        self.session.source.reset()
        self._refresh()

    def _refresh(self) -> None:
        session = self.session
        self.query_one(InputStrip).show(session.entries, session.direction)
        self.query_one(MoveFeed).show(session.activations)

        status = Text()
        plural = "" if session.total_activations == 1 else "s"
        status.append(f"{session.total_activations} move{plural} from {session.total_inputs} inputs")
        if session.exact_input:
            status.append("   exact key tracking", style="dim green")
        else:
            status.append(f"   inferred holds, {session.hold_window_ms}ms window", style="dim")
        if session.policy is BufferPolicy.LOOSE:
            status.append("   loose buffer: inputs are reused between moves", style="yellow")
        advice = session.keyboard_advice
        if advice:
            status.append(f"\n⚠ {advice}", style="yellow")
        self.query_one("#status", Static).update(status)

    def action_reset(self) -> None:
        """Clear the input buffer and the feed."""
        self.session.reset()
        self._refresh()

    def action_toggle_policy(self) -> None:
        """Switch between spending inputs on activation and loose matching."""
        self.post_message(self.PolicyChanged(self.session.toggle_policy()))
        self._refresh()

    def action_toggle_movelist(self) -> None:
        """Show or hide the reference move list."""
        movelist = self.query_one(MoveList)
        movelist.display = not movelist.display

    def action_back(self) -> None:
        """Return to the setup screen."""
        self.dismiss(None)
