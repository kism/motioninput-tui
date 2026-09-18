"""Parser for the Martial Masters FAQ.

Three fixed columns throughout - the name to 25, the command to 50, the
author's notes after that::

    Surge Fist               qcf + P                  LP=short, HP=far
    Swift Push               hcb + LP after
                               landing a close

so the notes are simply cut away, and a command that wraps carries on in the
middle column with the name column left blank. Those wraps have to be joined
back on rather than dropped: Swift Push's command is ``hcb + LP`` on its own
line, which parses perfectly well into a half circle and is not the move.

Each character is a starred banner, then the same seven headings every time.
``Colors`` is the palette select and is skipped; the rest are moves.

The guide's four buttons are already ``LP``/``HP``/``LK``/``HK``, which is the
dialect :mod:`normalise` reads, so no command translation is needed at all -
only the button *families* narrow, since ``P`` here is a choice of two rather
than the Street Fighter three.

What this game mostly has is chains: a move that connects opens the next, and
the guide writes the next one indented under it. The indent is the whole
signal, so a row's parent is whatever sits above it at a shallower depth - and
that is what makes an indented ``qcf + K`` Master Huang's Heavy Axe rather than
the perfectly ordinary Grasshopper the same motion gives when nothing is open.
"""

import re
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from motioninput_tui.engine.notation import Button
from motioninput_tui.games.models import Category, Move
from motioninput_tui_datagen.common import (
    DASHED,
    ParseReport,
    build_move,
    finish_character,
    narrow_buttons,
    split_name_command,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from motioninput_tui.games.models import Character

SECTION_START = "3. Characters"
SECTION_END = "4. Conclusion"
"""The guide's own numbering disagrees with its table of contents, which
promises a Codes section the body does not have, so the end marker is the
heading as written rather than the one the contents predict."""

NAME_COLUMN = 25
NOTES_COLUMN = 50
"""Where the command column starts and ends. Both hold across the whole guide."""

PANEL_PUNCHES = frozenset({Button.LP, Button.HP})
PANEL_KICKS = frozenset({Button.LK, Button.HK})
"""The two of each this panel has, which is what ``P`` and ``K`` mean here."""

_BANNER = re.compile(r"^\*{5,}$")
_TITLE = re.compile(r"^\*\s+\d+\.\d+\s+(.+?)\s+\*$")

_HEADINGS = {
    "Throw": Category.THROW,
    "Throws": Category.THROW,
    "Basic Move": Category.COMMAND,
    "Basic Moves": Category.COMMAND,
    "Command Moves": Category.COMMAND,
    "Special Moves": Category.SPECIAL,
    # A stock buys these, but there is no cinematic freeze on one, so they are
    # read at once like any other special rather than as a super.
    "Shadow Moves": Category.SPECIAL,
    "Supers": Category.SUPER,
}
_SKIPPED_HEADING = "Colors"

_TRAILING_AIR = re.compile(r",?\s*\bin (?:the )?air\s*$", re.IGNORECASE)
"""``hcb + K in air``, where ``normalise`` only reads air as a leading prefix."""


@dataclass(frozen=True, slots=True)
class _Row:
    """One move row as the three columns give it, before it is parsed."""

    name: str
    command: str
    indent: int
    """How far the name is indented, which is how this guide writes a chain: a
    link sits deeper than the move it continues. The depths are not a fixed
    step - Master Huang's string runs 0, 2, 3, 5 - so only the order matters."""


def parse(text: str) -> tuple[list[Character], ParseReport]:
    """Extract every character and their moves from the Martial Masters FAQ."""
    report = ParseReport()
    characters: list[Character] = []

    name = ""
    category: Category | None = None
    moves: list[Move] = []
    chain: list[_Row] = []

    def flush() -> None:
        character = finish_character(name, "", moves, report)
        if character is not None:
            characters.append(character)

    for line in _joined(_section(text)):
        stripped = line.strip()
        title = _TITLE.match(stripped)
        if title is not None:
            flush()
            name, moves, category, chain = title.group(1).strip(), [], None, []
        elif stripped in _HEADINGS or stripped == _SKIPPED_HEADING:
            category, chain = _HEADINGS.get(stripped), []
        elif category is not None:
            row = _row(line)
            if row is not None:
                moves.append(_move(row, category, report, name, _parent(chain, row)))

    flush()
    return characters, report


def _parent(chain: list[_Row], row: _Row) -> str:
    """The move this row continues, and keep the stack of open ones current.

    A row indented past the one above it is its follow-up; one at the same
    depth or shallower closes however many strings it has stepped back out of.
    ``chain`` is edited in place, so the caller's stack carries to the next row.
    """
    while chain and chain[-1].indent >= row.indent:
        chain.pop()
    parent = chain[-1].name if chain else ""
    chain.append(row)
    return parent


def _section(text: str) -> list[str]:
    """The character section, taken from the last of the two headings that say so.

    The table of contents at the top of the file spells the same words.
    """
    lines = text.splitlines()
    start = [index for index, line in enumerate(lines) if line.strip() == SECTION_START][-1]
    end = next((index for index in range(start + 1, len(lines)) if lines[index].strip() == SECTION_END), len(lines))
    return lines[start:end]


def _joined(lines: list[str]) -> Iterator[str]:
    """The section's lines with each wrapped command folded back onto its row.

    Folding them here is what lets the loop above treat every move as one line,
    and it matters for more than tidiness: Swift Push's first line reads
    ``hcb + LP after``, which on its own normalises into an ordinary half
    circle. It is the continuation that says the move needs a hit first.
    """
    row = ""
    for line in lines:
        if _passthrough(line) or line[:NAME_COLUMN].strip():
            if row:
                yield row
            row = "" if _passthrough(line) else line[:NOTES_COLUMN].rstrip()
            if not row:
                yield line
        elif row:
            tail = line[NAME_COLUMN:NOTES_COLUMN].strip()
            row = f"{row} {tail}" if tail else row
    if row:
        yield row


def _passthrough(line: str) -> bool:
    """Whether a line goes through whole rather than being cut to its columns.

    Blanks, rules and banner edges carry no move at all; a character's title
    runs the full width of the banner, so cutting it at the notes column would
    take the closing asterisk :data:`_TITLE` matches on off the end of it.
    """
    stripped = line.strip()
    return not stripped or bool(DASHED.match(line)) or bool(_BANNER.match(stripped)) or bool(_TITLE.match(stripped))


def _row(line: str) -> _Row | None:
    """One folded line split into its name and its command."""
    entry = split_name_command(line)
    if entry is None:
        return None
    return _Row(name=entry[0], command=entry[1], indent=len(line) - len(line.lstrip()))


def _move(row: _Row, category: Category, report: ParseReport, character: str, parent: str) -> Move:
    """One move row, parsed and put back onto this game's four buttons."""
    name, command = row.name, row.command
    move = build_move(name, _to_shorthand(command), report, character, category, follows=parent)
    if move.motion is None:
        return replace(move, command=command)
    buttons = narrow_buttons(move.motion.buttons, PANEL_PUNCHES, PANEL_KICKS)
    return replace(move, command=command, motion=replace(move.motion, buttons=buttons, notation=command))


def _to_shorthand(command: str) -> str:
    """Rewrite one command into the dialect ``normalise`` reads."""
    if _TRAILING_AIR.search(command):
        return f"In air, {_TRAILING_AIR.sub('', command)}"
    return command
