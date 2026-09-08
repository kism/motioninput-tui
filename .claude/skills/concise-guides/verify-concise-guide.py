#!/usr/bin/env python
"""Check a condensed guide against the full one it came from.

The concise guides are Markdown now, not a verbatim copy of the FAQ's
fixed-width move lists, so this can no longer parse both files and diff the
rosters. Instead, for a game that already has a parser, it parses the *full*
guide for the characters and move names the trainer expects, then checks how
many of those names survived into the Markdown. A name counts as present if it
appears as a run of words anywhere in the concise text, ignoring case,
punctuation and spacing. For a game with no parser yet only the size is checked.

Run from the repository root::

    .venv/bin/python .claude/skills/concise-guides/verify-concise-guide.py [game ...]
"""

import re
import sys
from pathlib import Path

from motioninput_tui.datagen import hsf2, sfa3, sfiii3

PARSERS = {"hsf2": hsf2.parse, "sfa3": sfa3.parse, "sfiii3": sfiii3.parse}
REFERENCES = Path("references")
MIN_RATIO = 0.02
"""Below this fraction of the original, the condensation ate the guide."""
MIN_CHARACTER_COVERAGE = 1.0
"""Every character must still be named somewhere in the Markdown."""
MIN_MOVE_COVERAGE = 0.85
"""Most move names must still be findable; reformatting notation loses a few."""


def read(path: Path) -> str:
    """Read a guide, tolerating the odd byte these FAQs are full of."""
    return path.read_text(encoding="utf-8", errors="replace")


def normalise(text: str) -> str:
    """Lowercase, and reduce every run of non-alphanumerics to a single space."""
    return re.sub(r"[^a-z0-9]+", " ", text.lower())


def coverage(names: list[str], haystack: str, label: str, floor: float) -> bool:
    """Print how many names survived into the normalised haystack; True if enough did."""
    missing = [name for name in names if (needle := normalise(name).strip()) and needle not in haystack]
    hits = len(names) - len(missing)
    ratio = hits / len(names) if names else 1.0
    print(f"    {label}: {hits}/{len(names)} found ({ratio:.0%})")
    if missing:
        print(f"    missing {label}: {missing[:20]}")
    return ratio >= floor


def check(game: str) -> bool:
    """Report on one game. False means something is wrong."""
    source, concise = REFERENCES / f"{game}.txt", REFERENCES / f"{game}_concise.md"
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
        print(f"{game}: {size}, no parser yet so only size checked")
        return True

    characters, _ = parse(full_text)
    haystack = normalise(concise_text)
    print(f"{game}: {size}")
    ok = coverage([c.name for c in characters], haystack, "characters", MIN_CHARACTER_COVERAGE)
    ok &= coverage([move.name for c in characters for move in c.moves], haystack, "moves", MIN_MOVE_COVERAGE)
    print(f"    {'names survived' if ok else 'NAMES MISSING'}")
    return ok


def main() -> int:
    """Check the games named, or every guide that has a condensed version."""
    games = sys.argv[1:] or sorted(path.name.removesuffix("_concise.md") for path in REFERENCES.glob("*_concise.md"))
    if not games:
        print("No condensed guides found. Run make-concise-guide.sh first.")
        return 1
    results = [check(game) for game in games]
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
