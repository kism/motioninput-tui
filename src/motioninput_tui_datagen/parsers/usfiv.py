"""Parser for the Ultra Street Fighter IV FAQ.

Move lists look like::

     EX  Change of Direction             qcf + P, then...
     I   Soulless                        qcf,qcf + PPP [AB]
     II  Breathless                      qcf,qcf + KKK

The shorthand dialect is the Alpha 3 / 3rd Strike one, so the closest parser is
``sfiii3``. The differences: the character headings carry a Japanese-name
parenthetical (``AKUMA … (GOUKI in JPN)``), and chained specials are written as
a parent line ending ``, then...`` followed by indented ``- `` follow-ups. The
follow-ups are skipped rather than ending the character's list.
"""

import re
from dataclasses import replace

from motioninput_tui.games.models import Category, Character
from motioninput_tui_datagen.common import DASHED, ParseReport, build_move, finish_character, split_name_command

SECTION_START = "3.  CHARACTER MOVELISTS"
SECTION_END = "3.  SECRETS AND TRICKS"

_HEADER = re.compile(r"^ ?([A-Z][A-Z0-9.'\- ]{1,30}?)(?:\s+\([^)]*\))?\s*$")
_MOVE = re.compile(r"^ {1,6}(?:(EX|III|II|I|any)\s+)?(\S.*?) {2,}(\S.*)$")
_STOP = re.compile(r"^\s*(Target Combos|Link Combos|Combos)\s*:")
_SUPER_FLAGS = frozenset({"I", "II", "III", "any"})
_SUPER_ARTS = frozenset({"I", "II", "III"})
"""``I`` / ``II`` are the two Ultra Combos; ``EX`` marks an EX special."""


def parse(text: str) -> tuple[list[Character], ParseReport]:
    """Extract every character and their moves from the USFIV FAQ."""
    report = ParseReport()
    characters: list[Character] = []
    lines = _section(text)

    name = ""
    moves: list = []
    collecting = False

    for index, line in enumerate(lines):
        header = _match_header(lines, index)
        if header is not None:
            character = finish_character(name, "", moves, report)
            if character is not None:
                characters.append(character)
            name = header
            moves = []
            collecting = True
            continue

        if not collecting:
            continue
        if _STOP.match(line):
            collecting = False
            continue

        entry = _match_move(line)
        if entry is None:
            continue
        flag, raw_name, command = entry
        category = Category.SUPER if flag in _SUPER_FLAGS else None
        moves.append(
            replace(
                build_move(raw_name, command, report, name, category),
                super_art=flag if flag in _SUPER_ARTS else "",
            )
        )

    character = finish_character(name, "", moves, report)
    if character is not None:
        characters.append(character)
    return characters, report


def _match_move(line: str) -> tuple[str | None, str, str] | None:
    """Split a move line into its flag column, name and command.

    Follow-ups of a chained special (``- Second Low  - f + K``, sometimes with
    the flag column filled in) and prose notes are dropped here rather than
    ending the character's list.
    """
    if line.lstrip().startswith("- "):
        return None
    match = _MOVE.match(line.rstrip())
    if match is None:
        return None
    flag, raw_name, command = match.groups()
    if raw_name.startswith("- ") or raw_name[:1].islower():
        return None
    if split_name_command(f"{raw_name}  {command}") is None:
        return None
    return flag, raw_name.strip(), command.strip()


def _section(text: str) -> list[str]:
    lines = text.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if SECTION_START in line and "TABLE" not in line)
        start = next(i for i in range(start + 1, len(lines)) if SECTION_START in lines[i])
    except StopIteration:
        start = 0
    end = next((i for i in range(start + 1, len(lines)) if SECTION_END in lines[i]), len(lines))
    return lines[start:end]


def _match_header(lines: list[str], index: int) -> str | None:
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
    return name
