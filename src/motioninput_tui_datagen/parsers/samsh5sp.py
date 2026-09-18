"""Parser for the Samurai Shodown V Special FAQ.

Command first, then the name, then a column saying whether the move needs a
weapon equipped (``E``), needs you unarmed (``U``), or does not care (``-``)::

    ------------------------------------------------------------------------
    BASARA KUBIKIRI
    ------------------------------------------------------------------------

    qcf + S                        Chisashi                                E
    qcb + C (hold)                 Kage Sui                                -
     _move b / f                   Zengo Idou                              -
    qcf + CD                    R^ Kagemai: Yumebiki                       E

The directions are already the dialect ``normalise`` reads (``qcf``, ``f,d,df``,
``Charge``), so unlike the KoF guides this one needs no translation there. The
buttons are the work: this is a Neo Geo panel but not a Neo Geo *game*, so
A and B are the weak and medium slash, ``AB`` the strong one, C the kick and D
the dodge — none of the punch/kick families the SF notation assumes. ``S``
means any slash, which is A, B or both.

``R^`` and ``Z^`` mark the moves that need a full Rage gauge, which is this
game's super meter, so they are what sets :attr:`Category.SUPER`. They sit in a
fixed column at the head of the name, and a long enough command runs into it
with only one space, so the marker rather than the column gap is what splits
the two fields.
"""

import re
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from motioninput_tui.games.models import Category
from motioninput_tui_datagen.common import DASHED, ParseReport, build_move, finish_character
from motioninput_tui_datagen.neogeo import to_neo_panel

if TYPE_CHECKING:
    from motioninput_tui.games.models import Character, Move

# The table of contents lists the heading once too; the movelists are second.
SECTION_START = "3.  CHARACTER MOVELISTS"
SECTION_END = "4.  GAMEPLAY NOTES"

_HEADER = re.compile(r"^\s*([A-Z][A-Z0-9'. -]{1,40}?)(?:\s{2,}\([^)]*\))?\s*$")
"""A name, optionally followed by the nickname Gaira is the only one to have."""

_STOP = re.compile(r"^\s*Cancel chart\b")

_WEAPON = re.compile(r"\s+[EU?-]\s*$")
"""The trailing column: needs a weapon (E), needs to be unarmed (U), neither
(-), or the guide is unsure (?). One name is long enough to leave it a single
space, so this cannot key off the column gap."""

_RAGE = re.compile(r"\s+(R\^|Z\^)\s+")
"""Needs a full Rage gauge, this game's super meter. Also the field separator
for the lines that have one, since a long command leaves only a single space
in front of it."""

_COLUMNS = re.compile(r"\s{2,}")

_FOLLOW_ON = "_"
"""Marks a line as continuing the move above it. The guide uses the indent to
say which move that is, so a run of them nests."""

_SET_MEMBER = re.compile(r"^\*\s+")
"""Marks a move as one of a numbered set -- Yoshitora's six Tachi, Rera's
Shikite. It is a note about the name, not part of it. The same star inside a
command ("use all * moves") is prose and stays."""

# A B AB are the slashes, C the kick, D the dodge. The mapping is arbitrary but
# has to be one-to-one, so neogeo.to_neo_panel can put it back on A B C D.
_BUTTONS = {"A": "LP", "B": "LK", "C": "HP", "D": "HK"}
_BUTTON_TOKEN = re.compile(r"(?<![A-Za-z])(S|any|[ABCD]{1,4})(?![A-Za-z])")


def parse(text: str) -> tuple[list[Character], ParseReport]:
    """Extract every character and their moves from the SSV Special FAQ."""
    report = ParseReport()
    characters: list[Character] = []
    lines = _section(text)

    name = ""
    moves: list[Move] = []
    chain: list[_Row] = []
    collecting = False

    for index, line in enumerate(lines):
        header = _match_header(lines, index)
        if header is not None:
            character = finish_character(name, "", moves, report)
            if character is not None:
                characters.append(character)
            name, moves, chain = header, [], []
            collecting = True
            continue

        if not collecting:
            continue
        if _STOP.match(line) or line.lstrip().startswith("- "):
            collecting = False
            continue

        entry = _split(line.rstrip())
        if entry is None:
            continue
        moves.append(_slash_move(entry, report, name, _parent(chain, entry)))

    character = finish_character(name, "", moves, report)
    if character is not None:
        characters.append(character)
    return characters, report


@dataclass(frozen=True, slots=True)
class _Row:
    """One move line, before its command is read."""

    indent: int
    """Where the line starts. A follow-up is written deeper than the move it
    continues, and Enja's Rikudou Rekka runs 1, 2, 4, so only the order counts."""
    command: str
    name: str
    rage: bool


def _split(line: str) -> _Row | None:
    """Pull a move line apart into its command, its name, and whether it rages."""
    if not line.startswith(" ") or not line.strip():
        return None
    body = _WEAPON.sub("", line).rstrip()
    indent = len(body) - len(body.lstrip())

    marker = _RAGE.search(body)
    if marker is not None:
        command, move_name = body[: marker.start()], body[marker.end() :]
        return _Row(indent, command.strip(), _SET_MEMBER.sub("", move_name.strip()), rage=True)

    parts = _COLUMNS.split(body.strip(), maxsplit=1)
    if len(parts) < 2:  # ruff: ignore[magic-value-comparison] - a command and a name
        return None
    return _Row(indent, parts[0].strip(), _SET_MEMBER.sub("", parts[1].strip()), rage=False)


def _parent(chain: list[_Row], row: _Row) -> str:
    """The move this row continues, and keep the stack of open ones current.

    The underscore says a row is a follow-up and the indent says of what: the
    nearest line above it that starts further left. A row without one closes
    whatever was open, so a plain move never inherits the string before it.
    """
    while chain and chain[-1].indent >= row.indent:
        chain.pop()
    parent = chain[-1].name if chain and row.command.startswith(_FOLLOW_ON) else ""
    chain.append(row)
    return parent


def _slash_move(row: _Row, report: ParseReport, character: str, parent: str) -> Move:
    """Build a move from a slash-panel command, keeping the guide's notation."""
    category = Category.SUPER if row.rage else None
    move = build_move(row.name, _to_shorthand(row.command), report, character, category, follows=parent)
    if move.motion is None:
        return replace(move, command=row.command)
    return replace(move, command=row.command, motion=to_neo_panel(move.motion, row.command))


def _to_shorthand(command: str) -> str:
    """Rewrite the buttons into the dialect normalise reads, directions as they are."""
    # The underscore only marks the line as a follow-up; what is left of it is
    # an ordinary command, and which move it follows is the indent's business.
    text = command.lstrip().removeprefix(_FOLLOW_ON)
    # "when near" is this guide's spelling of the range qualifier normalise knows.
    return _BUTTON_TOKEN.sub(_button, text).replace("when near", "when close")


def _button(match: re.Match[str]) -> str:
    group = match.group(1)
    if group == "S":  # any slash: A, B, or the two together
        return "LP / LK"
    if group == "any":
        return "LP / LK / HP / HK"
    return " + ".join(_BUTTONS[letter] for letter in group)


def _section(text: str) -> list[str]:
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if SECTION_START in line]
    start = starts[-1] if starts else 0
    end = next((i for i in range(start + 1, len(lines)) if SECTION_END in lines[i]), len(lines))
    return lines[start:end]


def _match_header(lines: list[str], index: int) -> str | None:
    """A character header is a name on its own between two dashed rules."""
    if index == 0 or index + 1 >= len(lines):
        return None
    if not DASHED.match(lines[index - 1]) or not DASHED.match(lines[index + 1]):
        return None
    match = _HEADER.match(lines[index].rstrip())
    return match.group(1).strip() if match is not None else None
