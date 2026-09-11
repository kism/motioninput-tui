"""The status line under a session: what about how inputs are read needs attention."""

from typing import TYPE_CHECKING

from rich.text import Text
from textual.widgets import Static

from motioninput_tui.engine.recognizer import BufferPolicy

if TYPE_CHECKING:
    from motioninput_tui.engine.session import TrainingSession


class StatusBar(Static):
    """Warnings about the device and the rules, and gone when there are none."""

    DEFAULT_CSS = """
    StatusBar { height: auto; padding: 0 1; color: $warning; border-top: solid $panel; }
    """

    def show(self, session: TrainingSession) -> None:
        """Say what needs saying about ``session``, or hide if nothing does."""
        notes: list[str] = []
        if session.gamepad_waiting:
            notes.append("no gamepad detected — plug one in")
        elif not session.exact_input:
            notes.append(f"inferred holds, {session.hold_window_ms}ms window")
        if session.policy is BufferPolicy.LOOSE:
            notes.append("loose buffer: inputs are reused between moves")
        if session.ruleset.lenient_half_circles:
            notes.append("relaxed half circles")
        lines = ["   ".join(notes)] if notes else []
        if session.keyboard_advice:
            lines.append(f"⚠ {session.keyboard_advice}")
        self.update(Text("\n".join(lines), style="yellow"))
        self.display = bool(lines)
