"""Parser for the Sailor Moon S / SuperS FAQ.

One guide covers both SNES games, so each entry says which one it belongs to: a
leading ``(S Only)`` or ``(SS Only)`` marker, or neither when both games have
the move. This is the S game, so the SuperS-only entries are dropped, and so is
Sailor Saturn, whose heading marks her as being in the sequel alone.

The guide writes forward as ``T``, for towards, which means nothing anywhere
else in the trainer. It is rewritten to ``F`` before the command is stored, so
the move list shows the translation rather than the guide's own letter - the
same bargain the KoF 2001 roster makes with that guide's numpad notation, and
the game's notes say so. That rewrite is also all the direction handling needed:
once towards is forward, every letter this guide uses is already the token
:mod:`normalise` reads, since it lowers the command anyway.

Its four attack buttons are named in words, and are translated separately. The
button requirement that comes back is then narrowed to the four the panel
actually has - "any punch" is two buttons here, not three.

An entry is a blank-line separated block rather than a line, because it wraps
over as many lines as it needs and an aside in brackets follows it inside the
same block. A marker can end up on one line with the command on the next, so
blocks are reflowed into one string before anything is matched against them.
"""

import re
from dataclasses import replace
from typing import TYPE_CHECKING

from motioninput_tui.engine.notation import Button
from motioninput_tui.games.models import Category
from motioninput_tui_datagen.common import DASHED, ParseReport, build_move, finish_character, narrow_buttons

if TYPE_CHECKING:
    from collections.abc import Iterator

    from motioninput_tui.games.models import Character, Move

SECTION_START = "Individual Special Moves"
SECTION_END = "Version History"

PANEL_PUNCHES = frozenset({Button.LP, Button.HP})
PANEL_KICKS = frozenset({Button.LK, Button.HK})
"""The SNES pad's two of each, which is what ``P`` and ``K`` mean in this game."""

HEADING_LINES = 2
"""A character heading is its name with a dashed rule under it."""

_SEQUEL = "SuperS"
_SEQUEL_ONLY = re.compile(r"^\(SS Only\)")
_MARKER = re.compile(r"^\((?:S|SS) Only\):?\s*")
_DESPERATION = re.compile(r"^Desperation:?\s*")
_PARENTHETICAL = re.compile(r"\([^)]*\)")
_ASIDE = re.compile(r"\(.*$", re.DOTALL)
"""Everything from where an entry's commentary opens. A command is only ever the
part in front of it, which is worth saying as "cut here" rather than as "strip
the brackets": the asides nest, and run to paragraphs, so pairing them off would
leave the prose between one aside's inner bracket and the next stranded in the
command - which is what the move list would then show the player."""

_ATTACK = re.compile(r"\b(?:Punch|Kick)\b")
"""What tells a move apart from the notes and the dashes: it ends in a button."""

_FORWARD = {"UT": "UF", "DT": "DF", "T": "F"}
_TOWARDS = re.compile(rf"\b({'|'.join(_FORWARD)})\b")
"""The guide's towards, and the two diagonals built on it. Nothing else it
writes needs touching: ``B``, ``D``, ``U`` and their diagonals already spell the
tokens ``normalise`` reads."""

_BUTTONS: list[tuple[re.Pattern[str], str]] = [
    # The strong one or the weak one, which is this guide's way of writing
    # "any punch"; the strong one alone is the heavy button.
    (re.compile(r"\bStrong Punch or Punch\b"), "any Punch"),
    (re.compile(r"\bStrong Kick or Kick\b"), "any Kick"),
    (re.compile(r"\bStrong Punch\b"), "HP"),
    (re.compile(r"\bStrong Kick\b"), "HK"),
]

_THEN = re.compile(r"\bthen\b")
"""The guide's charges read "hold X then Y", and ``normalise`` reads "then" as a
follow-up condition and drops the move; a comma is how the other guides write it."""


def parse(text: str) -> tuple[list[Character], ParseReport]:
    """Extract every S-game character and their moves from the Sailor Moon FAQ."""
    report = ParseReport()
    characters: list[Character] = []

    name = ""
    moves: list[Move] = []
    skipping = False

    for block in _blocks(text):
        heading = _heading(block)
        if heading is not None:
            if not skipping:
                character = finish_character(name, "", moves, report)
                if character is not None:
                    characters.append(character)
            name, moves = _character_name(heading), []
            skipping = _SEQUEL in heading
            continue

        if not name or skipping:
            continue
        entry = _entry(" ".join(line.strip() for line in block))
        if entry is not None:
            moves.append(_move(*entry, report, name))

    if not skipping:
        character = finish_character(name, "", moves, report)
        if character is not None:
            characters.append(character)
    return characters, report


def _section(text: str) -> list[str]:
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if line.strip() == SECTION_START), 0)
    end = next((i for i in range(start + 1, len(lines)) if lines[i].strip() == SECTION_END), len(lines))
    return lines[start:end]


def _blocks(text: str) -> Iterator[list[str]]:
    """The section's entries, one block each.

    A blank line ends a block, except where the guide runs two entries together
    with none between them - which it does for the character who has one
    desperation in each game. A game marker only ever opens an entry, so one
    arriving part way through a block starts the next instead of joining it.
    """
    block: list[str] = []
    for line in _section(text):
        if not line.strip():
            if block:
                yield block
                block = []
            continue
        if block and _MARKER.match(line.strip()):
            yield block
            block = []
        block.append(line)
    if block:
        yield block


def _heading(block: list[str]) -> str | None:
    """The character a block names, if it is a heading rather than a move."""
    if len(block) >= HEADING_LINES and DASHED.match(block[1]):
        return block[0].strip()
    return None


def _character_name(heading: str) -> str:
    """The S-game name out of a heading that gives both games' versions of her."""
    return _PARENTHETICAL.sub("", heading.split("/", maxsplit=1)[0]).strip()


def _entry(text: str) -> tuple[str, str, bool] | None:
    """One reflowed block as a name, a command and whether it is the desperation.

    Split on the *last* colon: an entry can carry its game marker and the word
    Desperation in front of the name, and an alternative name in brackets after
    it, all of them colon-separated.
    """
    if _SEQUEL_ONLY.match(text) or text.startswith("NOTE:"):
        return None

    name, colon, command = _MARKER.sub("", text).rpartition(":")
    if not colon or not _ATTACK.search(command):
        return None

    desperation = bool(_DESPERATION.match(name))
    name = _PARENTHETICAL.sub("", _DESPERATION.sub("", name)).strip()
    command = _ASIDE.sub("", command).strip().rstrip(".").strip()
    command = _TOWARDS.sub(lambda match: _FORWARD[match.group()], command)
    if not name or not command:
        return None
    return name, command, desperation


def _move(name: str, command: str, desperation: bool, report: ParseReport, character: str) -> Move:  # ruff: ignore[boolean-type-hint-positional-argument]
    """One entry, parsed in Street Fighter notation and put back on this panel."""
    category = Category.SUPER if desperation else None
    move = build_move(name, _to_shorthand(command), report, character, category)
    if move.motion is None:
        return replace(move, command=command)
    buttons = narrow_buttons(move.motion.buttons, PANEL_PUNCHES, PANEL_KICKS)
    return replace(move, command=command, motion=replace(move.motion, buttons=buttons, notation=command))


def _to_shorthand(command: str) -> str:
    """Rewrite one command into the dialect ``normalise`` reads."""
    text = command
    for pattern, replacement in _BUTTONS:
        text = pattern.sub(replacement, text)
    return _THEN.sub(",", text)
