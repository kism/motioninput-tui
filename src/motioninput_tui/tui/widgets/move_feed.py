"""The list of moves the engine believes came out."""

from typing import TYPE_CHECKING

from rich.text import Text
from textual.widgets import Static

from motioninput_tui.engine.recognizer import FollowUpStatus

from .input_strip import CATEGORY_STYLES

if TYPE_CHECKING:
    from collections.abc import Iterable

    from motioninput_tui.engine.recognizer import Activation, FollowUp
    from motioninput_tui.notation_styles import Notation


class MoveFeed(Static):
    """Newest activation at the top, with anything else that also matched."""

    DEFAULT_CSS = """
    MoveFeed {
        padding: 0 1;
        height: 1fr;
    }
    """

    def show(self, activations: Iterable[Activation], notation: Notation) -> None:
        """Redraw the feed, with each move's input written in ``notation``."""
        text = Text(no_wrap=True, overflow="ellipsis")
        entries = list(activations)
        if not entries:
            text.append("Nothing yet. Do a motion and press an attack button.", style="dim italic")
            self.update(text)
            return

        for index, activation in enumerate(entries):
            move = activation.move
            marker = "▸ " if index == 0 else "  "
            style = CATEGORY_STYLES.get(move.category, "white")
            if index:
                style = f"dim {style}"
            text.append(marker, style=style)
            text.append(f"{move.name:<30}", style=style)
            text.append(f"{notation.write_move(move):<28}", style="dim")
            if activation.follow_up is not None:
                append_follow_up(text, activation.follow_up, newest=index == 0)
            elif activation.also_matched:
                text.append(f"also: {', '.join(activation.also_matched)}", style="dim italic")
            text.append("\n")
        self.update(text)


def append_follow_up(text: Text, follow_up: FollowUp, *, newest: bool) -> None:
    """The second-phase prompt or verdict for a two-phase move.

    Shared with the trainer's full-screen panel, which hides this feed.
    """
    done, needed = follow_up.got, follow_up.needed
    if follow_up.status is FollowUpStatus.COMPLETE:
        text.append("✓" * needed, style="bold green")
    elif follow_up.status is FollowUpStatus.MISSED:
        text.append("✓" * done + "·" * (needed - done), style="yellow")
        if newest:
            text.append("  missed", style="yellow")
    elif newest:
        text.append("●" * done + "○" * (needed - done), style="bold yellow")
        if follow_up.frozen:
            # The activation cinematic is still running and the game is
            # reading nothing, so prompting for taps would teach the
            # opposite of what the freeze exists to show.
            text.append("  wait...", style="bold yellow")
        else:
            verb = "tap" if follow_up.rhythm else "mash"
            text.append(f"  {verb} {follow_up.button_label}!", style="bold yellow")
    else:
        text.append("●" * done + "○" * (needed - done), style="dim yellow")
