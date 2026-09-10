"""Parser for the King of Fighters '98 FAQ.

Each character is a name line, a bio, then four boxed sections::

                          o----------------------o
                                SPECIAL MOVES
                          o----------------------o

    114 Shiki Aragami: d, df, f + A
    100 Shiki Oniyaki: f, d, df + P

so this guide says outright which moves are supers and the blank-line grouping
``super_tail`` infers it from elsewhere is not needed. Characters are separated
by ``---`` or a team banner, and the bio is ignored because collection only
starts at the first section heading.

The commands themselves are the same dialect the 2001 guide writes, down to the
``d~u`` charges and the ``(d, df, f)x2`` repeats, so :mod:`neogeo` reads them
and maps the buttons back onto the Neo Geo's A B C D panel for both.

Only the 41 characters the arcade release selects are taken; the EX section's
alternate versions of characters already listed are skipped, as is the
unplayable Omega Rugal.
"""

import re
from dataclasses import replace
from typing import TYPE_CHECKING

from motioninput_tui.games.models import Category, Move
from motioninput_tui_datagen.common import ParseReport, build_move, finish_character
from motioninput_tui_datagen.neogeo import to_neo_panel, to_shorthand, unmodelled

if TYPE_CHECKING:
    from motioninput_tui.games.models import Character

SECTION_END = "CREDITS"

_BANNER = re.compile(r"^\*{5,}(.+?)\*{5,}$")
_SEPARATOR = "---"
# The banner is the character's team. Two need help: one is a typo, and the
# other names a section this takes only the Real Orochi Team out of.
_TEAMS = {"PROTAGANIST TEAM": "Hero Team", "EX CHARACTERS": "Real Orochi Team"}
_WORD = re.compile(r"[\w']+")

_HEADINGS = {
    "THROWS": Category.THROW,
    "COMMAND MOVES": Category.COMMAND,
    "SPECIAL MOVES": Category.SPECIAL,
    "SUPER MOVES": Category.SUPER,
}

_FOLLOWS_ON = "follows on from the move its name trails"

# Alternate versions of characters already in the roster, plus the boss the
# guide itself marks as unplayable.
_ALT_VERSION = re.compile(r"^(EX |95' |Omega )")
_ASIDE = re.compile(r"\s*\(.*\)\s*$")


def parse(text: str) -> tuple[list[Character], ParseReport]:
    """Extract every character and their moves from the KoF '98 FAQ."""
    report = ParseReport()
    characters: list[Character] = []

    name = ""
    team = ""
    category: Category | None = None
    moves: list[Move] = []
    expect_name = False
    skipping = False

    def flush() -> None:
        character = finish_character(name, team, moves, report)
        if character is not None:
            characters.append(character)

    for line in _section(text):
        stripped = line.strip()
        banner = _BANNER.match(stripped)
        if banner is not None or stripped == _SEPARATOR:
            flush()
            name, moves, category, expect_name, skipping = "", [], None, True, False
            if banner is not None:
                team = _team(banner.group(1).strip())
            continue

        if expect_name and stripped:
            name = _ASIDE.sub("", stripped)
            expect_name = False
            skipping = bool(_ALT_VERSION.match(name))
            continue

        if skipping:
            continue

        if stripped in _HEADINGS:
            category = _HEADINGS[stripped]
            continue

        if category is not None and ":" in stripped:
            moves.append(_move(stripped, category, moves, report, name))

    flush()
    return characters, report


def _team(banner: str) -> str:
    """The team name a banner carries, in the casing the roster displays."""
    return _TEAMS.get(banner, _WORD.sub(lambda word: word.group().capitalize(), banner))


def _move(line: str, category: Category, so_far: list[Move], report: ParseReport, character: str) -> Move:
    """One ``Name: command`` row, in the Neo Geo's own A B C D notation.

    Split on the *last* colon: a move name can carry one of its own, as
    ``Ura 108 Shiki: Orochinagi: d, db, b, db, d, df, f + P`` does.
    """
    name, _, command = line.rpartition(":")
    name, command = name.strip(), command.strip()

    reason = _FOLLOWS_ON if _follows_on(name, so_far) else unmodelled(command)
    if reason:
        # Kept in the move list, struck through, rather than reduced to
        # whatever motion happens to be inside it.
        report.note(character, name, reason)
        return Move(name=name, command=command, category=category)

    move = build_move(name, to_shorthand(command), report, character, category)
    if move.motion is None:
        return replace(move, command=command)
    return replace(move, command=command, motion=to_neo_panel(move.motion, command))


def _follows_on(name: str, so_far: list[Move]) -> bool:
    """Whether the move a name trails after is one this character already has.

    ``Gliding Buster: Strong Grand Saber: f + D`` is Leona's Grand Saber
    follow-up, not a command move: splitting on the last colon leaves the
    parent move's name on the end of this one.
    """
    _, colon, tail = name.rpartition(":")
    return bool(colon) and any(move.name in tail for move in so_far)


def _section(text: str) -> list[str]:
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if _BANNER.match(line.strip())), 0)
    end = next((i for i in range(start, len(lines)) if lines[i].strip() == SECTION_END), len(lines))
    return lines[start:end]
