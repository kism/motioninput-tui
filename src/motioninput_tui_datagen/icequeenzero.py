"""The page furniture the Ice Queen Zero movelists share.

Samurai Shodown II and The Last Blade 2 are the same author's FAQs and are laid
out identically: a ``MOVELISTS`` banner, then one block per character, its name
between two ``+---+`` rules, then boxed headings over ``Name: command`` rows::

    +---------------------+
             YUKI
    +---------------------+

                          o----------------------o
                                SPECIAL MOVES
                          o----------------------o

    HyouJin: d, df, f + A or B

So :func:`blocks` walks the page for both and hands each parser its characters
and their rows, leaving each to say what its own game's buttons and markers
mean. The KoF '98 guide is the same author again but not the same furniture --
it groups characters into teams under banner rules -- so it walks itself.

The commands are the same dialect throughout, which :mod:`neogeo` reads.
"""

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

    from motioninput_tui.games.models import Category

SECTION_START = "MOVELISTS"
SECTION_END = "CREDITS"

_RULE = re.compile(r"^\+-{3,}\+$")
"""The rules a character's name sits between."""

_ASIDE = re.compile(r"\s+-\s+.*$")
"""A note the author hung off a name, as on Last Blade 2's Kojiroh."""


def blocks(text: str, headings: Mapping[str, Category]) -> list[tuple[str, list[tuple[Category, str]]]]:
    """Every character in the movelist section, with their ``(category, line)`` rows.

    Rows are the lines under a heading in ``headings``; anything under a
    heading the caller does not name is left out, which is how the front matter
    and the credits stay out of a roster.
    """
    lines = _section(text)
    out: list[tuple[str, list[tuple[Category, str]]]] = []

    name = ""
    rows: list[tuple[Category, str]] = []
    category: Category | None = None

    for index, line in enumerate(lines):
        stripped = line.strip()
        header = _header(lines, index)
        if header is not None:
            if rows:
                out.append((name, rows))
            name, rows, category = header, [], None
            continue

        if stripped in headings:
            category = headings[stripped]
            continue

        if category is not None and ":" in stripped:
            rows.append((category, stripped))

    if rows:
        out.append((name, rows))
    return out


def _header(lines: list[str], index: int) -> str | None:
    """A character name, if one sits between two ``+---+`` rules here."""
    if index == 0 or index + 1 >= len(lines):
        return None
    if not _RULE.match(lines[index - 1].strip()) or not _RULE.match(lines[index + 1].strip()):
        return None
    return _ASIDE.sub("", lines[index].strip()) or None


def _section(text: str) -> list[str]:
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if line.strip() == SECTION_START), 0)
    end = next((i for i in range(start + 1, len(lines)) if lines[i].strip() == SECTION_END), len(lines))
    return lines[start:end]
