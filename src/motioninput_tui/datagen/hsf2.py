"""Parser for the Hyper Street Fighter II guide.

This guide spells directions out in full::

    - Ryu -
    ------------------------------------------------------------------
    Fireball       - D, DF, F + any Punch
    Dragon Punch   - F, D, DF + any Punch
"""

import re
from typing import TYPE_CHECKING

from .common import DASHED, ParseReport, build_move, finish_character

if TYPE_CHECKING:
    from motioninput_tui.games.models import Character

_HEADER = re.compile(r"^- ([A-Z][A-Za-z0-9.'\- ]{1,20}) -\s*$")
_MOVE = re.compile(r"^([A-Za-z][A-Za-z0-9 .'/]*?)\s+-\s+(\S.*)$")
_STOP = re.compile(r"^\s*(Combos|Notes|Best version|Basic Strategy|How to pick)\s*:?")


def parse(text: str) -> tuple[list[Character], ParseReport]:
    """Extract every character and their moves from the Hyper SF2 guide."""
    report = ParseReport()
    characters: list[Character] = []
    lines = text.splitlines()

    name = ""
    moves: list = []
    collecting = False

    for index, line in enumerate(lines):
        header = _HEADER.match(line)
        if header is not None and index + 1 < len(lines) and DASHED.match(lines[index + 1]):
            character = finish_character(name, "", moves, report)
            if character is not None:
                characters.append(character)
            name = header.group(1).strip()
            moves = []
            collecting = True
            continue

        if not collecting:
            continue
        if _STOP.match(line):
            collecting = False
            continue
        if DASHED.match(line):
            continue

        match = _MOVE.match(line.rstrip())
        if match is None:
            continue
        move_name, command = match.group(1).strip(), match.group(2).strip()
        # Continuation lines are indented under the previous command.
        if line.startswith(" "):
            continue
        moves.append(build_move(move_name, command, report, name))

    character = finish_character(name, "", moves, report)
    if character is not None:
        characters.append(character)
    return characters, report
