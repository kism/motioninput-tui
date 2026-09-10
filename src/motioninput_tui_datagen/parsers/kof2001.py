"""Parser for the King of Fighters 2001 FAQ by Ice Queen Zero.

This replaced the numpad guide the game used to be built from. That one wrote
``2363214+K`` in fixed-width columns and never said what a move *was*, so
specials and DMs had to be told apart by the blank line between them. This one
names every group outright::

    Yuri Sakazaki
    Fighting Style : Kyokugen Karate
    ...
                          o----------------------o
                                SUPER MOVES
                          o----------------------o

    Hien Rekkou (DM): d, df, f, df, d, db, b + P
    Hien Hou'ou Kyaku (DM): d, df, f, df, d, db, b + K
    Hien Hou'ou Kyaku (SDM): d, df, f, df, d, db, b + BD

A DM is a super because the guide says so, and the commands are already the
``d, df, f + P`` dialect :mod:`normalise` reads. Only two things need rewriting
first: ``(d, df, f)x2`` repeats, which ``normalise`` would otherwise strip as a
parenthetical aside and lose the motion with, and the Neo Geo button letters.

Sections run THROWS, COMMAND MOVES, SPECIAL MOVES, SUPER MOVES, once each, so a
heading that does not follow the last one is the first heading of the next
character. The name sits above a ``Fighting Style`` bio, except for the two
bosses, which have none.

Follow-ups are written by naming the move they come out of
(``128 Shiki Kono Kizu: 114 Shiki Aragami, d, df, f + P``). The trainer has no
model for a chain, so those are marked conditional and keep the guide's wording
rather than being quietly reduced to the quarter circle on the end of them.

The Neo Geo panel is A B C D. Commands are translated into the Street Fighter
dialect ``normalise`` reads and the resulting requirement mapped back by
:mod:`motioninput_tui_datagen.neogeo`, exactly as the KoF '98 parser does.
"""

import re
from dataclasses import replace
from typing import TYPE_CHECKING

from motioninput_tui.games.models import Category, Move
from motioninput_tui_datagen.common import ParseReport, build_move, finish_character
from motioninput_tui_datagen.neogeo import to_neo_panel, to_shorthand, unmodelled

if TYPE_CHECKING:
    from motioninput_tui.games.models import Character

SECTION_START = "TEAM STORY AND MOVES"
SECTION_END = "CREDITS"

_BOX = re.compile(r"^\s*o-{5,}o\s*$")
"""The rule drawn above and below every heading in this guide."""

_SECTIONS: dict[str, str] = {
    "THROWS": Category.THROW,
    "COMMAND MOVES": Category.COMMAND,
    "SPECIAL MOVES": Category.SPECIAL,
    "SUPER MOVES": Category.SUPER,
}
"""The guide's own grouping, which is the whole reason for using it: a DM is a
super because it is written under ``SUPER MOVES``, not because of its motion."""

_ORDER = tuple(_SECTIONS)

_TEAM = re.compile(r"^\s*~~\s*(.+?)\s*~~\s*$")
"""``~~Art of Fighting Team~~`` above each team, which becomes the title."""

_BIO = re.compile(r"^\s*Fighting Style\s*:")

_ALT_MODE = re.compile(r"^\s*={3,}\s*\S.*?\s*={3,}\s*$")
"""May Lee's two stances are ``====Hero Mode====`` blocks. The trainer has no
model for a stance and both would key the same, so only the first is taken."""

_ENDS_SECTION = re.compile(r"^\s*(-{3,}|\+{3,}|={3,}|Striker Move\b|Notes\b)")
"""What closes a character's last section: the striker line and its notes."""


def parse(text: str) -> tuple[list[Character], ParseReport]:
    """Extract every character and their moves from the KoF 2001 FAQ."""
    report = ParseReport()
    characters: list[Character] = []
    lines = _section(text)

    state = _Roster(report)
    index = 0
    while index < len(lines):
        heading = _boxed_heading(lines, index)
        if heading is not None:
            state.heading(heading, characters)
            index += 3
            continue
        state.line(lines[index])
        index += 1

    state.finish(characters)
    return characters, report


class _Roster:
    """The walk's state: which character and section the reader is inside.

    ``pending`` is every line since the last heading. At a character boundary
    that is the block between two move lists, which is where the name is.
    """

    def __init__(self, report: ParseReport) -> None:
        """Start outside any character."""
        self.report = report
        self.name = ""
        self.team = ""
        self.moves: list[Move] = []
        self.category = ""
        self.previous = ""
        self.pending: list[str] = []
        self.skipping = False

    def heading(self, heading: str, characters: list[Character]) -> None:
        """Take a boxed heading, starting a new character when the order resets."""
        section = _SECTIONS.get(heading)
        if section is None:  # INTRODUCTION, GLOSSARY and the rest of the front matter
            self.category, self.previous, self.pending = "", "", []
            return
        if not self.previous or _ORDER.index(heading) <= _ORDER.index(self.previous):
            found = _character_name(self.pending)
            if found is not None:
                self.finish(characters)
                self.name, self.moves = found, []
                self.skipping = bool(_ALT_MODE.match(found))
        self.category, self.previous, self.pending = section, heading, []

    def line(self, line: str) -> None:
        """Take one ordinary line: a move, a team heading, or block furniture."""
        team = _TEAM.match(line)
        if team is not None:
            self.team = team.group(1)
        if _ENDS_SECTION.match(line):
            self.category = ""
        if self.category and not self.skipping:
            move = self._move(line)
            if move is not None:
                self.moves.append(move)
                return
        self.pending.append(line)

    def _move(self, line: str) -> Move | None:
        """One ``Name: command`` row, or None when the line is not one.

        Split on the *last* colon: a move name can carry one of its own, as
        ``Ura 108 Shiki: Orochinagi(DM): d, db, b, db, d, df, f + P`` does.
        """
        name, _, command = line.rpartition(":")
        name, command = name.strip(), command.strip()
        if not name or not command:
            return None
        reason = unmodelled(command)
        if reason:
            # Kept in the list under its own heading, struck through, rather
            # than reduced to whatever motion happens to be inside it.
            self.report.note(self.name, name, reason)
            return Move(name=name, command=command, category=self.category)
        move = build_move(name, to_shorthand(command), self.report, self.name, category=self.category)
        if move.motion is None:
            return replace(move, command=command)
        return replace(move, command=command, motion=to_neo_panel(move.motion, command))

    def finish(self, characters: list[Character]) -> None:
        """Wrap up the character being read, if there is one."""
        character = finish_character(self.name, self.team, self.moves, self.report)
        if character is not None:
            characters.append(character)


def _boxed_heading(lines: list[str], index: int) -> str | None:
    """The heading opening at ``index``, if a boxed one does."""
    if index + 2 >= len(lines) or not _BOX.match(lines[index]) or not _BOX.match(lines[index + 2]):
        return None
    return lines[index + 1].strip()


def _character_name(pending: list[str]) -> str | None:
    """The character name in the block between two move lists.

    Almost every character has it directly above a ``Fighting Style`` bio; the
    two bosses have no bio, so it is the last plain line instead. Lines carrying
    a colon are bio entries and the striker line, never the name.
    """
    for index, line in enumerate(pending):
        if _BIO.match(line):
            above = [text.strip() for text in pending[:index] if text.strip()]
            return above[-1] if above else None
    plain = [line.strip() for line in pending if line.strip() and ":" not in line]
    return plain[-1] if plain else None


def _section(text: str) -> list[str]:
    """The movelist half of the guide, between its front and back matter."""
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if SECTION_START in line), 0)
    end = next((i for i in range(start + 1, len(lines)) if SECTION_END in lines[i]), len(lines))
    return lines[start:end]
