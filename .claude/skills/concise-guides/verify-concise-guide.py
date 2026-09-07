#!/usr/bin/env python
"""Check a condensed guide against the full one it came from.

For a game that already has a parser, the strongest evidence that nothing the
trainer needs was thrown away is that the parser gets the same roster out of
both files. For a game with no parser yet, which is the usual reason for
condensing a guide in the first place, there is nothing to compare against, so
only the obvious signs of a bad condensation are checked.

Run from the repository root::

    .venv/bin/python .claude/skills/concise-guides/verify-concise-guide.py [game ...]
"""

from __future__ import annotations

import sys
from pathlib import Path

from motioninput_tui.datagen import hsf2, sfa3, sfiii3

PARSERS = {"hsf2": hsf2.parse, "sfa3": sfa3.parse, "sfiii3": sfiii3.parse}
REFERENCES = Path("references")
MIN_RATIO = 0.02
"""Below this fraction of the original, the condensation ate the guide."""


def read(path: Path) -> str:
    """Read a guide, tolerating the odd byte these FAQs are full of."""
    return path.read_text(encoding="utf-8", errors="replace")


def check(game: str) -> bool:
    """Report on one game. False means something is wrong."""
    source, concise = REFERENCES / f"{game}.txt", REFERENCES / f"{game}_concise.txt"
    if not concise.is_file():
        print(f"{game}: no {concise.name}")
        return False
    if not source.is_file():
        print(f"{game}: no {source.name} to compare against")
        return False

    full_text, concise_text = read(source), read(concise)
    ratio = len(concise_text) / len(full_text)
    size = f"{len(concise_text):,} of {len(full_text):,} bytes ({ratio:.0%})"
    if ratio < MIN_RATIO:
        print(f"{game}: {size} - too little came back, condense it again")
        return False

    parse = PARSERS.get(game)
    if parse is None:
        print(f"{game}: {size}, no parser yet so nothing to compare")
        return True

    full_characters, full_report = parse(full_text)
    concise_characters, concise_report = parse(concise_text)
    same = [character.key for character in full_characters] == [character.key for character in concise_characters]
    print(f"{game}: {size}, {'same roster' if same else 'ROSTER DIFFERS'}")
    print(f"    full:    {full_report.summary()}")
    print(f"    concise: {concise_report.summary()}")
    if not same:
        lost = sorted({c.key for c in full_characters} - {c.key for c in concise_characters})
        gained = sorted({c.key for c in concise_characters} - {c.key for c in full_characters})
        print(f"    lost: {lost}  gained: {gained}")
    return same


def main() -> int:
    """Check the games named, or every guide that has a condensed version."""
    games = sys.argv[1:] or sorted(path.name.removesuffix("_concise.txt") for path in REFERENCES.glob("*_concise.txt"))
    if not games:
        print("No condensed guides found. Run make-concise-guide.sh first.")
        return 1
    results = [check(game) for game in games]
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
