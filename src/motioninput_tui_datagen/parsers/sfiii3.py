"""Parser for the 3rd Strike FAQ.

Move lists look like::

     EX  Flash Chop                 qcf + P
     I   Hyper Bomb                 Rotate 360 + P   x1
"""

import re

from motioninput_tui.games.models import Category, Character
from motioninput_tui_datagen.common import DASHED, ParseReport, build_move, finish_character, split_name_command

SECTION_START = "2.  CHARACTER MOVELISTS"
SECTION_END = "3.  SECRETS AND TRICKS"

_HEADER = re.compile(r"^ ?([A-Z][A-Z0-9.'\- ]{0,30})(?:,\s*(.+))?$")
_MOVE = re.compile(r"^ {1,6}(?:(EX|III|II|I|any)\s+)?(\S.*?) {2,}(\S.*)$")
_STOP = re.compile(r"^\s*(Target Combos|Link Combos|Combos)\s*:")
_SUPER_FLAGS = frozenset({"I", "II", "III", "any"})


def parse(text: str) -> tuple[list[Character], ParseReport]:
    """Extract every character and their moves from the 3rd Strike FAQ."""
    report = ParseReport()
    characters: list[Character] = []
    lines = _section(text)

    name = ""
    title = ""
    moves: list = []
    collecting = False

    for index, line in enumerate(lines):
        header = _match_header(lines, index)
        if header is not None:
            character = finish_character(name, title, moves, report)
            if character is not None:
                characters.append(character)
            name, title = header
            moves = []
            collecting = True
            continue

        if not collecting:
            continue
        if _STOP.match(line) or line.lstrip().startswith("- "):
            collecting = False
            continue

        match = _MOVE.match(line.rstrip())
        if match is None:
            continue
        flag, raw_name, command = match.groups()
        # A move name always starts upper-case (or "..." for a follow-up); a
        # lower-case start is prose, like Q's three lines about abridged names.
        if raw_name[:1].islower():
            continue
        parts = split_name_command(f"{raw_name}  {command}")
        if parts is None:
            continue
        category = Category.SUPER if flag in _SUPER_FLAGS else None
        moves.append(build_move(raw_name.strip(), command.strip(), report, name, category))

    character = finish_character(name, title, moves, report)
    if character is not None:
        characters.append(character)
    return characters, report


def _section(text: str) -> list[str]:
    lines = text.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if SECTION_START in line and "TABLE" not in line)
        start = next(i for i in range(start + 1, len(lines)) if SECTION_START in lines[i])
    except StopIteration:
        start = 0
    end = next((i for i in range(start + 1, len(lines)) if SECTION_END in lines[i]), len(lines))
    return lines[start:end]


def _match_header(lines: list[str], index: int) -> tuple[str, str] | None:
    """A character header is a name sandwiched between two dashed rules."""
    if index == 0 or index + 1 >= len(lines):
        return None
    if not DASHED.match(lines[index - 1]) or not DASHED.match(lines[index + 1]):
        return None
    match = _HEADER.match(lines[index].rstrip())
    if match is None:
        return None
    name = match.group(1).strip()
    if not name or name == "TABLE OF CONTENTS":
        return None
    return name, (match.group(2) or "").strip()
