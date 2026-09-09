"""Parser for the King of Fighters 2001 FAQ.

Unlike the same author's KoF '98 guide, this one is written in numpad notation
with the command in the *first* column and the name in the second::

    ------------------------------------------------------------------------
    HEIDERN                                                   [ Ikari Team ]
    ------------------------------------------------------------------------

    N>4/6+C                Lead Belcher
    6+B                    Shooter Narnagel
    236+P                  Cross Cutter
    236236+P               FINAL BRINGER

Numbers are stick positions with the player on the left, so 6 is forward and
``236`` is a quarter circle forward. The guide's own legend gives the rest:
``.`` charges in the first direction, ``()x2`` repeats the bracketed motion,
``_`` is an additional input, ``~`` a range of directions, and the marker
prefixes and suffixes are ``N>`` near, ``F>`` at throw range, ``A>`` must be in
the air, ``T>`` must tap, against optional ``<A`` / ``<T`` / ``<H``.

The mandatory markers are translated (``A>`` becomes an ``In air,`` prefix so
the air check fires); the optional ones are dropped. ``_`` chains, ``~`` ranges
and ``H>`` held buttons are left as they are, so they fail to normalise and are
reported as skipped rather than silently mis-parsed.

The Neo Geo panel is A B C D. Commands are translated into the Street Fighter
dialect ``normalise`` reads and the resulting requirement mapped back by
:mod:`motioninput_tui_datagen.neogeo`, exactly as the KoF '98 parser does.
"""

import re
from dataclasses import replace
from typing import TYPE_CHECKING

from motioninput_tui_datagen.common import DASHED, ParseReport, build_move, finish_character, super_tail
from motioninput_tui_datagen.neogeo import TO_SHORTHAND, to_neo_panel

if TYPE_CHECKING:
    from motioninput_tui.games.models import Character, Move

# The table of contents lists the heading once too; the movelists are second.
SECTION_START = "3. TEAM MOVELISTS"
SECTION_END = "4. GAMEPLAY NOTES"

# ``K'  (pronounced "kay dash")   [ Hero Team ]`` — the parenthetical is a
# pronunciation note, the bracketed tail is the team, which becomes the title.
_HEADER = re.compile(r"^\s*([A-Z][A-Z0-9'() ]*?)\s*(?:\([^)]*\)\s*)?\[\s*([^\]]+?)\s*\]\s*$")
_MOVE = re.compile(r"^ (\S+)\s{2,}(\S.*)$")
_STOP = re.compile(r"^\s*(Super Cancels|Critical Wire|Counter Wire|Striker Action|Cancelables)\b")

_NUMPAD = {"1": "db", "2": "d", "3": "df", "4": "b", "5": "n", "6": "f", "7": "ub", "8": "u", "9": "uf"}

_ALT_VERSION = "(HERO)"
"""May Lee's second heading is a stance-switch moveset for the same slot,
entered mid-match with ABC. The trainer has no model for a stance, and its key
would collide with the normal version's."""

_MARKERS = {"A>": "In air, ", "N>": "when close, ", "F>": "", "T>": ""}
"""Mandatory prefixes. Only the air one changes how a move is recognised; the
range and tap markers are notes to the player."""

_OPTIONAL = re.compile(r"<[AHT]")
"""``<A`` can be used in air, ``<T`` can tap, ``<H`` can hold: all optional, so
none of them changes the input the move needs."""

_UNMODELLED = re.compile(r"[_~]|H>")
"""An additional input off the previous move, a range of directions, or a
button that ``H>`` says must be *held* (as opposed to optional ``<H``). The
engine treats a button press as momentary, so a held button reads exactly like
a tapped one: ``236+H>P`` would be indistinguishable from the ``236+P`` beside
it. Left unmodelled, it keeps the guide's wording and is struck through."""

_REPEATED = re.compile(r"^\((\d+)\)x2$")


def parse(text: str) -> tuple[list[Character], ParseReport]:
    """Extract every character and their moves from the KoF 2001 FAQ."""
    report = ParseReport()
    characters: list[Character] = []
    lines = _section(text)

    name = ""
    title = ""
    # Moves are collected in blank-line-delimited groups; the guide lists the
    # DMs and SDMs last, so `super_tail` tags that final group as supers.
    groups: list[list[Move]] = [[]]
    collecting = False

    for index, line in enumerate(lines):
        header = _match_header(lines, index)
        if header is not None:
            character = finish_character(name, title, super_tail(groups), report)
            if character is not None:
                characters.append(character)
            name, title = header
            groups = [[]]
            collecting = _ALT_VERSION not in line
            continue

        if not collecting:
            continue
        if _STOP.match(line) or line.lstrip().startswith("- "):
            collecting = False
            continue

        match = _MOVE.match(line.rstrip())
        if match is None:
            if not line.strip() and groups[-1]:
                groups.append([])
            continue
        groups[-1].append(_neo_move(match.group(2).strip(), match.group(1), report, name))

    character = finish_character(name, title, super_tail(groups), report)
    if character is not None:
        characters.append(character)
    return characters, report


def _neo_move(move_name: str, command: str, report: ParseReport, character: str) -> Move:
    """Build a move from a numpad command, keeping the guide's own notation."""
    move = build_move(move_name, _to_shorthand(command), report, character)
    if move.motion is None:
        return replace(move, command=command)
    return replace(move, command=command, motion=to_neo_panel(move.motion, command))


def _to_shorthand(command: str) -> str:
    """Rewrite ``236+P`` as ``d,df,f + any punch``, the dialect normalise reads.

    Returns the command unchanged when it is not a plain motion, so it fails to
    normalise and is reported as skipped rather than silently mis-parsed.
    """
    body, prefix = _OPTIONAL.sub("", command), ""
    for marker, replacement in _MARKERS.items():
        if marker in body:
            body = body.replace(marker, "")
            prefix += replacement
    if _UNMODELLED.search(body):
        return command

    directions, _, buttons = body.partition("+")
    repeated = _REPEATED.match(directions)
    if repeated is not None:
        directions = repeated.group(1) * 2

    charged = "." in directions
    written = " / ".join(_directions(part) for part in directions.split("/"))
    if not buttons or not written:
        return command
    return f"{prefix}{'Charge ' if charged else ''}{written} + {_buttons(buttons)}"


def _directions(part: str) -> str:
    """One alternative's stick positions, as the letter tokens normalise knows."""
    digits = part.replace(".", "")
    if not digits or not digits.isdigit():
        return ""
    return ",".join(_NUMPAD[digit] for digit in digits)


def _buttons(part: str) -> str:
    """``P`` -> ``any punch``, ``AC`` -> ``LP + HP``, ``C/D`` -> ``HP / HK``."""
    return " / ".join(" + ".join(TO_SHORTHAND.get(letter, letter) for letter in option) for option in part.split("/"))


def _section(text: str) -> list[str]:
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if SECTION_START in line]
    start = starts[-1] if starts else 0
    end = next((i for i in range(start + 1, len(lines)) if SECTION_END in lines[i]), len(lines))
    return lines[start:end]


def _match_header(lines: list[str], index: int) -> tuple[str, str] | None:
    """A character header is ``NAME  [ Team ]`` between two dashed rules."""
    if index == 0 or index + 1 >= len(lines):
        return None
    if not DASHED.match(lines[index - 1]) or not DASHED.match(lines[index + 1]):
        return None
    match = _HEADER.match(lines[index].rstrip())
    if match is None:
        return None
    return match.group(1).strip(), match.group(2).strip()
