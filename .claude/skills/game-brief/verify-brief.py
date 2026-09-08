#!/usr/bin/env python
"""Check a game brief against the guide and the generated roster.

A brief is analysis, not a copy of the guide, so this cannot diff move lists.
It checks three things instead:

* every required ``##`` section is present;
* for a game that has a parser, every character the parser finds in the full
  guide is named somewhere in the brief;
* for a game whose roster JSON exists, the brief's ``predicted_trainable``
  frontmatter value is within 15 points of the real figure.

A game with no parser yet gets only the structural check.

Run from the repository root::

    .venv/bin/python .claude/skills/game-brief/verify-brief.py [game ...]
"""

import json
import re
import sys
from pathlib import Path

from motioninput_tui.datagen.__main__ import PARSERS

BRIEFS = Path(__file__).parent / "briefs"
REFERENCES = Path("references")
DATA = Path("src/motioninput_tui/games/data")

REQUIRED_SECTIONS = (
    "## Roster",
    "## Guide anatomy",
    "## Notation & engine fit",
    "## Ruleset rationale",
    "## Test seeds",
)
TRAINABLE_TOLERANCE = 15
"""Percentage points the prediction may be off before it counts as wrong."""


def read(path: Path) -> str:
    """Read a file, tolerating the odd byte these FAQs are full of."""
    return path.read_text(encoding="utf-8", errors="replace")


def normalise(text: str) -> str:
    """Lowercase, and reduce every run of non-alphanumerics to a single space."""
    return re.sub(r"[^a-z0-9]+", " ", text.lower())


def frontmatter_int(text: str, key: str) -> int | None:
    """Pull ``key: <int>`` out of the leading ``--- ... ---`` block."""
    match = re.search(rf"^{key}:\s*(\d+)\s*$", text, re.MULTILINE)
    return int(match.group(1)) if match else None


def actual_trainable(game: str) -> int | None:
    """The trainable percentage in the committed roster JSON, if there is one."""
    path = DATA / f"{game}.json"
    if not path.is_file():
        return None
    moves = [move for character in json.loads(read(path))["characters"] for move in character["moves"]]
    if not moves:
        return None
    return round(sum("motion" in move for move in moves) / len(moves) * 100)


def check(game: str) -> bool:
    """Report on one brief. False means something is wrong."""
    brief = BRIEFS / f"{game}.md"
    if not brief.is_file():
        print(f"{game}: no {brief.name}")
        return False
    text = read(brief)
    print(f"{game}: {len(text):,} bytes")

    ok = True
    missing = [section for section in REQUIRED_SECTIONS if section not in text]
    if missing:
        print(f"    MISSING SECTIONS: {missing}")
        ok = False
    else:
        print("    sections: all present")

    parse = PARSERS.get(game)
    if parse is None:
        print("    no parser yet, skipping character and trainable checks")
        return ok

    source = REFERENCES / f"{game}.txt"
    if not source.is_file():
        print(f"    no {source.name} to list characters from")
        return False
    haystack = normalise(text)
    characters, _ = parse(read(source))
    unnamed = [c.name for c in characters if normalise(c.name).strip() not in haystack]
    hits = len(characters) - len(unnamed)
    print(f"    characters: {hits}/{len(characters)} named" + (f", missing {unnamed[:15]}" if unnamed else ""))
    ok &= not unnamed

    predicted = frontmatter_int(text, "predicted_trainable")
    actual = actual_trainable(game)
    if predicted is None:
        print("    predicted_trainable: not in frontmatter")
        ok = False
    elif actual is None:
        print(f"    predicted_trainable: {predicted}% (no roster JSON to compare)")
    else:
        off = abs(predicted - actual)
        verdict = "ok" if off <= TRAINABLE_TOLERANCE else f"OFF BY {off}pp"
        print(f"    trainable: predicted {predicted}%, actual {actual}% ({verdict})")
        ok &= off <= TRAINABLE_TOLERANCE

    return ok


def main() -> int:
    """Check the games named, or every brief that exists."""
    games = sys.argv[1:] or sorted(path.stem for path in BRIEFS.glob("*.md"))
    if not games:
        print("No briefs found. Run make-brief.sh first.")
        return 1
    results = [check(game) for game in games]
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
