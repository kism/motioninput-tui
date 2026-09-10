"""Parser for the Samurai Shodown II FAQ.

:mod:`icequeenzero` walks the page, which this guide lays out exactly as the
Last Blade 2 one does. What is left is what this game means by its buttons and
its markers.

Two markers ride on a move name. ``*`` is a move that needs a full POW meter,
which is this game's super, and is the only thing here that says so. ``#`` is
the variant of a throw used against Earthquake, the one character who could not
be thrown until this game.

The panel is the Neo Geo's four buttons but not a Neo Geo brawler's: A and B
are the light and medium slash, C and D the light and medium kick, and pressing
a pair gives the heavy version of either. ``Slash`` and ``Kick`` are the
guide's way of saying "either of that pair", which is what the SF punch and
kick families mean, so they are written out as the pair before :mod:`neogeo`
translates the letters and maps everything back onto A B C D.
"""

import re
from dataclasses import replace
from typing import TYPE_CHECKING

from motioninput_tui.games.models import Category, Move
from motioninput_tui_datagen.common import ParseReport, build_move, finish_character
from motioninput_tui_datagen.icequeenzero import blocks
from motioninput_tui_datagen.neogeo import to_neo_panel, to_shorthand, unmodelled

if TYPE_CHECKING:
    from motioninput_tui.games.models import Character

_HEADINGS = {
    "THROWS": Category.THROW,
    "COMMAND MOVES": Category.COMMAND,
    "SPECIAL MOVES": Category.SPECIAL,
}

_POW = "*"
"""Needs a full POW meter: this game's super, and the only marker for one."""

_MARKERS = re.compile(r"[*#]+\s*$")
"""``*`` for the POW moves and ``#`` for the throws that are used against
Earthquake. Both trail the move name and neither is part of it."""

# A and B are the two slashes, C and D the two kicks, so the guide's "Slash"
# and "Kick" are exactly what the SF punch and kick families mean.
_PAIRS = re.compile(r"\b(slash|kick)\b", re.IGNORECASE)
_AS_PAIR = {"slash": "LP / LK", "kick": "HP / HK"}


def parse(text: str) -> tuple[list[Character], ParseReport]:
    """Extract every character and their moves from the Samurai Shodown II FAQ."""
    report = ParseReport()
    characters: list[Character] = []

    for name, rows in blocks(text, _HEADINGS):
        moves = [_slash_move(line, category, report, name) for category, line in rows]
        character = finish_character(name, "", moves, report)
        if character is not None:
            characters.append(character)

    return characters, report


def _slash_move(line: str, category: Category, report: ParseReport, character: str) -> Move:
    """One ``Name: command`` row, in the Neo Geo's own A B C D notation."""
    name, _, command = line.rpartition(":")
    name, command = name.strip(), command.strip()
    if _POW in name:
        category = Category.SUPER
    name = _MARKERS.sub("", name).strip()

    # A command opening with Slash or Kick opens with a button, which is all
    # `unmodelled` reads of the head; the letter it stands in for is arbitrary.
    reason = unmodelled(_PAIRS.sub("A", command))
    if reason:
        # Kept in the move list, struck through, rather than reduced to
        # whatever motion happens to be inside it.
        report.note(character, name, reason)
        return Move(name=name, command=command, category=category)

    move = build_move(name, to_shorthand(_PAIRS.sub(_pair, command)), report, character, category)
    if move.motion is None:
        return replace(move, command=command)
    return replace(move, command=command, motion=to_neo_panel(move.motion, command))


def _pair(match: re.Match[str]) -> str:
    return _AS_PAIR[match.group(1).lower()]
