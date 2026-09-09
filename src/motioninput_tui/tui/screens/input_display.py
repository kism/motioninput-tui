"""The input display: no game, no moves, just what the device is doing.

It runs on the same :class:`~motioninput_tui.engine.session.TrainingSession` as
the trainer, so directions are cleaned and holds inferred exactly as they are
when a move is on the line. Nothing is recognised; the panel is drawn instead.
"""

from typing import TYPE_CHECKING, ClassVar, override

from rich.text import Text
from textual.binding import Binding
from textual.containers import Center, Horizontal
from textual.screen import Screen
from textual.widgets import Footer, Static

from motioninput_tui.engine.session import TrainingSession, monotonic_ms
from motioninput_tui.tui.widgets.input_strip import InputStrip
from motioninput_tui.tui.widgets.panel import ButtonPads, DirectionGate

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from motioninput_tui.controls.buttons import ButtonSet
    from motioninput_tui.controls.layouts import ControlLayout
    from motioninput_tui.engine.notation import Button
    from motioninput_tui.games.models import Character, Game

TICK_HZ = 60


class InputDisplayScreen(Screen):
    """Draws the panel live: the gate, the buttons, and the input history."""

    BINDINGS: ClassVar = [
        Binding("escape", "back", "Change panel"),
        Binding("ctrl+r", "reset", "Reset"),
        Binding("ctrl+b", "app.settings", "Settings"),
        # Nothing here takes text input, so drop Screen's copy/paste bindings
        # from the key panel; ctrl+c stays as the quit shortcut.
        Binding("ctrl+c", "app.help_quit", show=False, system=True),
    ]

    DEFAULT_CSS = """
    InputDisplayScreen { layout: vertical; }
    InputDisplayScreen #banner { height: auto; padding: 0 1; background: $panel; }
    InputDisplayScreen #panel-area { height: 1fr; align: center middle; }
    InputDisplayScreen #panel { width: auto; height: auto; }
    InputDisplayScreen InputStrip { border-bottom: none; }
    InputDisplayScreen #status { height: auto; padding: 0 1; color: $text-muted; border-top: solid $panel; }
    """

    def __init__(
        self,
        game: Game,
        character: Character,
        layout: ControlLayout,
        buttons: ButtonSet,
        *,
        exact_input: bool = False,
    ) -> None:
        """Set a session up for this panel.

        ``character`` is the button set as it was picked; ``buttons`` is that
        set as the settings arrange it, which is what actually gets drawn.
        """
        super().__init__()
        self.session = TrainingSession(game, character, layout, exact_input=exact_input)
        self.character = character
        self.panel = buttons
        self._held: dict[Button, int] = {}
        """Buttons down, and when they went down. A terminal that reports
        releases empties this properly; without one they lapse like a hold."""

    @override
    def compose(self) -> ComposeResult:
        """The gate and the buttons side by side, over the input history."""
        yield Static(id="banner")
        with Center(id="panel-area"), Horizontal(id="panel"):
            yield DirectionGate()
            yield ButtonPads()
        yield InputStrip(id="strip")
        yield Static(id="status")
        yield Footer()

    def on_mount(self) -> None:
        """Paint the chrome and start the tick that expires holds."""
        self.title = f"Input display · {self.panel.name}"
        self.sub_title = self.session.layout.name
        self._paint_banner()
        self._refresh()
        self.set_interval(1 / TICK_HZ, self._tick)
        self.focus()

    def _paint_banner(self) -> None:
        session = self.session
        text = Text()
        text.append(self.panel.name, style="bold")
        if self.panel.note:
            text.append(f"  {self.panel.note}", style="dim italic")
        text.append(f"\nMove {session.layout.movement_help()}   Attack {session.layout.attack_help()}", style="dim")
        self.query_one("#banner", Static).update(text)

    def apply_panel(self, layout: ControlLayout, buttons: ButtonSet) -> None:
        """Take a rearranged panel, from the settings, without leaving it."""
        self.panel = buttons
        self.session.rebind(layout)
        self._held.clear()
        if self.is_mounted:
            self._paint_banner()
            self._refresh()

    def on_key(self, event) -> None:  # ruff: ignore[missing-type-function-argument] - textual.events.Key
        """Feed every bound key to the session before Textual sees it."""
        if event.key not in self.session.layout.bindings:
            return
        event.stop()
        event.prevent_default()
        button = self.session.layout.attacks.get(event.key)
        if button is not None:
            self._held[button] = monotonic_ms()
        self.session.press(event.key)
        self._refresh()

    def handle_release(self, key: str) -> None:
        """Called by the app when the terminal reports a key going back up."""
        if key not in self.session.layout.bindings:
            return
        button = self.session.layout.attacks.get(key)
        if button is not None:
            self._held.pop(button, None)
        self.session.release(key)
        self._refresh()

    def on_app_blur(self) -> None:
        """Drop everything held when the terminal loses focus."""
        self.session.source.reset()
        if self.session.gamepad is not None:
            self.session.gamepad.reset()
        self._held.clear()
        self._refresh()

    def _tick(self) -> None:
        changed = self.session.tick()
        if self._expire_buttons():
            changed = True
        if changed:
            self._refresh()

    def _expire_buttons(self) -> bool:
        """Let held buttons lapse when the terminal cannot report releases."""
        if self.session.exact_input or not self._held:
            return False
        cutoff = monotonic_ms() - self.session.hold_window_ms
        lapsed = [button for button, at_ms in self._held.items() if at_ms < cutoff]
        for button in lapsed:
            del self._held[button]
        return bool(lapsed)

    def _refresh(self) -> None:
        session = self.session
        direction = session.direction
        self.query_one(DirectionGate).show(direction)
        self.query_one(ButtonPads).show(session.layout, self._held)
        self.query_one(InputStrip).show(session.entries, direction)

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
        self._held.clear()
        self._refresh()

    def action_back(self) -> None:
        """Return to the setup screen."""
        self.dismiss(None)
