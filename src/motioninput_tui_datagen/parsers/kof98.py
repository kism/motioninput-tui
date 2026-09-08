"""Parser for the King of Fighters '98 FAQ.

Each character has a fixed-width "Short Moves List" between two bracketed
rules, in the same ``qcf + P`` shorthand Alpha 3 uses::

    ------------------------  [ Short Moves List ]  ------------------------

    Hatsugane                       When close, b / f + C
    114 Shiki: Aragami              qcf + A
    100 Shiki: Oniyaki              f,d,df + P
    Ura 108 Shiki: Orochi Nagi      qcb,hcf + P  (hold P to delay)

The Neo Geo panel is A B C D, not the Street Fighter six the normaliser and
rosters are written in. Commands are translated to that dialect for parsing
(A/C are the punches, B/D the kicks) and the resulting button requirement is
mapped back onto A B C D so it matches what the Neo Geo layout produces.

Only the 40-strong main roster and the Real Orochi Team are taken; the FAQ's
"Style Character" section is alternate versions of characters already listed.
"""

import re
from dataclasses import replace
from typing import TYPE_CHECKING

from motioninput_tui.engine.notation import ALL_BUTTONS, KICKS, PUNCHES, Button, ButtonRequirement
from motioninput_tui_datagen.common import DASHED, ParseReport, build_move, finish_character, split_name_command

if TYPE_CHECKING:
    from motioninput_tui.engine.motions import MotionSpec
    from motioninput_tui.games.models import Character, Move

# The table of contents lists the heading once too; the movelists are second.
SECTION_START = "2.  CHARACTER MOVELISTS"
SECTION_END = "4.  SECRETS AND TRICKS"

_HEADER = re.compile(r"^\s*([A-Z][A-Z0-9.'! -]{1,40}?)\s{2,}\(([^)]*)\)\s*$")
_ALT_VERSION = "Style Character"
_SHORT_LIST = "[ Short Moves List ]"
_BRACKET_RULE = re.compile(r"^\s*-{3,}\s*\[")
_SUBTITLE = re.compile(r"^\s*\[.*\]\s*$")

# Directions are lower case in this guide (``d,df,f``) and the button letters
# upper case (``+ C``), so a case-sensitive swap keeps the two apart.
_TO_SHORTHAND = {"A": "LP", "B": "LK", "C": "HP", "D": "HK", "P": "any punch", "K": "any kick"}
_BUTTON_LETTER = re.compile(r"(?<![A-Za-z])([ABCDPK])(?![A-Za-z])")

_NEO_PUNCHES = frozenset({Button.A, Button.C})
_NEO_KICKS = frozenset({Button.B, Button.D})
_TO_NEO = {
    Button.LP: Button.A,
    Button.MP: Button.A,
    Button.HP: Button.C,
    Button.LK: Button.B,
    Button.MK: Button.B,
    Button.HK: Button.D,
}
_NEO_ORDER = (Button.A, Button.B, Button.C, Button.D)


def parse(text: str) -> tuple[list[Character], ParseReport]:
    """Extract every character and their moves from the KoF '98 FAQ."""
    report = ParseReport()
    characters: list[Character] = []
    lines = _section(text)

    name = ""
    title = ""
    moves: list[Move] = []
    collecting = False
    skipping = False

    for index, line in enumerate(lines):
        header = _match_header(lines, index)
        if header is not None:
            character = finish_character(name, title, moves, report)
            if character is not None:
                characters.append(character)
            name, title = header
            moves = []
            collecting = False
            skipping = _ALT_VERSION in title
            continue

        if skipping:
            continue
        if _SHORT_LIST in line:
            collecting = True
            continue
        if not collecting:
            continue
        if _BRACKET_RULE.match(line):
            collecting = False
            continue

        parts = split_name_command(line)
        if parts is None:
            continue
        moves.append(_neo_move(parts[0], parts[1], report, name))

    character = finish_character(name, title, moves, report)
    if character is not None:
        characters.append(character)
    return characters, report


def _neo_move(move_name: str, command: str, report: ParseReport, character: str) -> Move:
    """Build a move from a Neo Geo command, keeping the A B C D notation."""
    move = build_move(move_name, _BUTTON_LETTER.sub(lambda m: _TO_SHORTHAND[m.group(1)], command), report, character)
    if move.motion is None:
        return replace(move, command=command)
    return replace(move, command=command, motion=_to_neo_panel(move.motion, command))


def _to_neo_panel(motion: MotionSpec, command: str) -> MotionSpec:
    """Put a motion's button requirement back onto the Neo Geo's A B C D."""
    return replace(motion, buttons=_neo_buttons(motion.buttons), notation=command.strip())


def _neo_buttons(requirement: ButtonRequirement) -> ButtonRequirement:
    count = requirement.count
    if requirement.allowed == PUNCHES:
        return ButtonRequirement(_NEO_PUNCHES, count, "P" * count)
    if requirement.allowed == KICKS:
        return ButtonRequirement(_NEO_KICKS, count, "K" * count)
    if requirement.allowed == ALL_BUTTONS:
        return ButtonRequirement(_NEO_PUNCHES | _NEO_KICKS, count, "any button")
    mapped = frozenset(_TO_NEO.get(button, button) for button in requirement.allowed)
    names = [button.value for button in _NEO_ORDER if button in mapped]
    return ButtonRequirement(mapped, count, ("+" if count >= len(names) else "/").join(names))


def _section(text: str) -> list[str]:
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if SECTION_START in line]
    start = starts[-1] if starts else 0
    end = next((i for i in range(start + 1, len(lines)) if SECTION_END in lines[i]), len(lines))
    return lines[start:end]


def _match_header(lines: list[str], index: int) -> tuple[str, str] | None:
    """A character header is ``NAME  (Team)`` under a dashed rule.

    The main roster closes with a second rule on the next line; the Real Orochi
    Team slips a ``[ bracketed subtitle ]`` in before that rule.
    """
    if index == 0:
        return None
    if not DASHED.match(lines[index - 1]):
        return None
    below = lines[index + 1 : index + 3]
    closed = bool(below) and (DASHED.match(below[0]) or (_SUBTITLE.match(below[0]) and _rule_at(below, 1)))
    if not closed:
        return None
    match = _HEADER.match(lines[index].rstrip())
    if match is None:
        return None
    return match.group(1).strip(), match.group(2).strip()


def _rule_at(below: list[str], offset: int) -> bool:
    return len(below) > offset and bool(DASHED.match(below[offset]))
