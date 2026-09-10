"""Parser for the Street Fighter Alpha 3 FAQ.

Move lists carry an ISM column in the first five characters::

    XAV  Rising Jaguar                   f,d,df + K
     A   Jaguar Revolver                 qcf,qcf + K
"""

import re
from typing import TYPE_CHECKING

from motioninput_tui_datagen.common import DASHED, ParseReport, build_move, finish_character, split_name_command

if TYPE_CHECKING:
    from motioninput_tui.games.models import Character

SECTION_START = "2.  CHARACTER MOVES LIST"
SECTION_END = "4.  SECRETS AND CODES"

ISM_COLUMN = 5
_HEADER = re.compile(r"^([A-Z][A-Z0-9.'\- ]{1,30})(?:\s+\([^)]*\))?$")
_STOP = re.compile(r"^\s*(Alpha Counter|Cancellable Attacks|V-ISM Variable|Combos)")


def parse(text: str) -> tuple[list[Character], ParseReport]:
    """Extract every character and their moves from the Alpha 3 FAQ."""
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
        if _STOP.match(line) or line.lstrip().startswith("- "):
            collecting = False
            continue

        entry = _match_move(line.rstrip())
        if entry is None:
            continue
        moves.append(build_move(entry[0], entry[1], report, name))

    character = finish_character(name, "", moves, report)
    if character is not None:
        characters.append(character)
    return characters, report


def _section(text: str) -> list[str]:
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if SECTION_START in line]
    start = starts[-1] if starts else 0
    end = next((i for i in range(start + 1, len(lines)) if SECTION_END in lines[i]), len(lines))
    return lines[start:end]


def _match_move(line: str) -> tuple[str, str] | None:
    """Strip the ISM column, then split the fixed-width name and command."""
    if len(line) <= ISM_COLUMN:
        return None
    ism, rest = line[:ISM_COLUMN], line[ISM_COLUMN:]
    if set(ism) - set("XAV "):
        return None
    if not set(ism) & set("XAV"):
        return None
    if not rest.startswith(" ") and not rest[:1].isalnum():
        return None
    return split_name_command(rest)


def _match_header(lines: list[str], index: int) -> str | None:
    if index == 0 or index + 1 >= len(lines):
        return None
    if not DASHED.match(lines[index - 1]) or not DASHED.match(lines[index + 1]):
        return None
    match = _HEADER.match(lines[index].rstrip())
    if match is None:
        return None
    return match.group(1).strip()
