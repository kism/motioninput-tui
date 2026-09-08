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
from dataclasses import replace
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

# A B AB are the slashes, C the kick, D the dodge. The mapping is arbitrary but
# has to be one-to-one, so neogeo.to_neo_panel can put it back on A B C D.
_BUTTONS = {"A": "LP", "B": "LK", "C": "HP", "D": "HK"}
_BUTTON_TOKEN = re.compile(r"(?<![A-Za-z])(S|any|[ABCD]{1,2})(?![A-Za-z])")


def parse(text: str) -> tuple[list[Character], ParseReport]:
    """Extract every character and their moves from the SSV Special FAQ."""
    report = ParseReport()
    characters: list[Character] = []
    lines = _section(text)

    name = ""
    moves: list[Move] = []
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

        entry = _split(line.rstrip())
        if entry is None:
            continue
        command, move_name, rage = entry
        moves.append(_slash_move(move_name, command, report, name, rage=rage))

    character = finish_character(name, "", moves, report)
    if character is not None:
        characters.append(character)
    return characters, report


def _split(line: str) -> tuple[str, str, bool] | None:
    """Pull a move line apart into its command, its name, and whether it rages."""
    if not line.startswith(" ") or not line.strip():
        return None
    body = _WEAPON.sub("", line).rstrip()

    marker = _RAGE.search(body)
    if marker is not None:
        command, move_name = body[: marker.start()], body[marker.end() :]
        return command.strip(), move_name.strip(), True

    parts = _COLUMNS.split(body.strip(), maxsplit=1)
    if len(parts) < 2:  # ruff: ignore[magic-value-comparison] - a command and a name
        return None
    return parts[0].strip(), parts[1].strip(), False


def _slash_move(move_name: str, command: str, report: ParseReport, character: str, *, rage: bool) -> Move:
    """Build a move from a slash-panel command, keeping the guide's notation."""
    category = Category.SUPER if rage else None
    move = build_move(move_name, _to_shorthand(command), report, character, category)
    if move.motion is None:
        return replace(move, command=command)
    return replace(move, command=command, motion=to_neo_panel(move.motion, command))


def _to_shorthand(command: str) -> str:
    """Rewrite the buttons into the dialect normalise reads, directions as they are.

    A follow-up keeps its leading underscore, so it fails to normalise and is
    reported as skipped rather than read as a move in its own right.
    """
    if command.lstrip().startswith("_"):
        return command
    # "when near" is this guide's spelling of the range qualifier normalise knows.
    return _BUTTON_TOKEN.sub(_button, command).replace("when near", "when close")


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
