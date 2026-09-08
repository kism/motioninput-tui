"""The list of moves the engine believes came out."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.text import Text
from textual.widgets import Static

from .input_strip import CATEGORY_STYLES

if TYPE_CHECKING:
    from collections.abc import Iterable

    from motioninput_tui.engine.recognizer import Activation
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
            if activation.also_matched:
                text.append(f"also: {', '.join(activation.also_matched)}", style="dim italic")
            text.append("\n")
        self.update(text)
