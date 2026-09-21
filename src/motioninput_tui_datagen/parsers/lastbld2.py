"""Parser for The Last Blade 2 FAQ.

The same author and the same page as the Samurai Shodown II guide, so
:mod:`icequeenzero` walks it and :mod:`neogeo` reads the commands. This one is
the plainest of the three SNK guides here: it names its supers outright under
``SUPER MOVES``, writes every button as a letter (no ``Slash``/``Kick`` words)
and hangs no markers off a move name -- the ``(DM)`` and ``(SDM)`` a super
carries are the guide's own wording and stay in the name, saying which meter it
wants.

The panel is the Neo Geo's four buttons: A and B are the weak and strong slash,
C the kick and D the repel, so :mod:`neogeo` maps them back the same way it
does for Samurai Shodown.
"""

from dataclasses import replace
from typing import TYPE_CHECKING

from motioninput_tui.games.models import Category, Move
from motioninput_tui_datagen.common import ParseReport, build_move, finish_character
from motioninput_tui_datagen.icequeenzero import blocks
from motioninput_tui_datagen.neogeo import split_parent, to_neo_panel, to_shorthand, unmodelled

if TYPE_CHECKING:
    from motioninput_tui.games.models import Character

_HEADINGS = {
    "SPECIAL MOVES": Category.SPECIAL,
    "SUPER MOVES": Category.SUPER,
}


def parse(text: str) -> tuple[list[Character], ParseReport]:
    """Extract every character and their moves from The Last Blade 2 FAQ."""
    report = ParseReport()
    characters: list[Character] = []

    for name, rows in blocks(text, _HEADINGS):
        # Accumulated rather than built in one go: a chain link names the move
        # it comes out of, and that has to already be in the list to be found.
        moves: list[Move] = []
        for category, line in rows:
            moves.append(_blade_move(line, category, report, name, moves))
        character = finish_character(name, "", moves, report)
        if character is not None:
            characters.append(character)

    return characters, report


def _blade_move(line: str, category: Category, report: ParseReport, character: str, so_far: list[Move]) -> Move:
    """One ``Name: command`` row, in the Neo Geo's own A B C D notation.

    This guide writes a chain the way the KoF pair do, as the move it continues
    then a comma then this half's own input (``Ittou Sogetsu: Ittou Shingetsu,
    f, d, df + B``), so :func:`neogeo.split_parent` reads it.
    """
    name, _, command = line.rpartition(":")
    name, command = name.strip(), command.strip()

    parent, own = split_parent(command, so_far)
    reason = unmodelled(own if parent else command)
    if reason:
        # Kept in the move list, struck through, rather than reduced to
        # whatever motion happens to be inside it.
        report.note(character, name, reason)
        return Move(name=name, command=command, category=category, follows=parent)

    move = build_move(name, to_shorthand(own or command), report, character, category, follows=parent)
    if move.motion is None:
        return replace(move, command=command)
    return replace(move, command=command, motion=to_neo_panel(move.motion, command))
