#!/usr/bin/env python3
"""Print Third Strike's command tables in a readable form.

The figures in ``SFIII3``'s ruleset come from these tables. This decodes them
straight out of the decompilation so they can be checked rather than trusted;
see ``docs/sfiii3-from-the-decomp.md`` for what the format means.

    ./scripts/decode-3s-commands.py ~/src/3s-decomp          # every character
    ./scripts/decode-3s-commands.py ~/src/3s-decomp ryu      # one of them

The decompilation is not vendored here and nothing in the trainer imports this;
it is the working out behind the numbers, kept so they can be re-derived.
"""

import re
import sys
from collections import Counter
from pathlib import Path

CMD_DATA = Path("src/anniversary/sf33rd/Source/Game/cmd_data.c")

# player_number order, from the per-character tables in Ck_Pass.c.
CHARACTERS = (
    "gill", "alex", "ryu", "yun", "dudley", "necro", "hugo", "ibuki", "elena", "oro",
    "yang", "ken", "sean", "urien", "gouki", "chun-li", "makoto", "q", "twelve", "remy",
)  # fmt: skip
TABLES = (
    "p0", "p1", "p2", "p3", "p4", "p5", "p6", "p7", "p8", "p9",
    "pA", "pB", "pC", "pD", "pE", "p10", "p11", "p12", "p13", "p14",
)  # fmt: skip

# The lever is four bits, normalised so that forward is towards the opponent.
LEVER = {0: "n", 1: "u", 2: "d", 4: "f", 8: "b", 5: "uf", 6: "df", 9: "ub", 10: "db"}

# Step type, as written in the data. It indexes chk_move_jp, which is off by
# one: type 1 runs check_0. Only the types the specials and supers use are
# named; the rest are parries, dashes and the other common commands.
STEP_TYPES = {
    1: "dir", 2: "charge", 4: "btn-charge", 5: "mash", 6: "lever+btn", 7: "rot4",
    8: "mash-p", 9: "mash-k", 23: "rot8", 27: "tap-release",
}  # fmt: skip

HEADER_WORDS = 12
STEP_WORDS = 4
END_OF_COMMAND = 28
SPECIALS_START = 20  # Slots below this are the common commands every character shares.
EXACT = 0x8000


def load(root: Path) -> tuple[dict[str, list[int]], dict[str, list[str]]]:
    """The `const s16` arrays and the 56-slot tables that name them."""
    text = (root / CMD_DATA).read_text(encoding="utf-8")
    arrays = {
        match[1]: [int(word) for word in match[2].replace("\n", " ").split(",") if word.strip()]
        for match in re.finditer(r"const s16 (\w+)\[\d+\]\s*=\s*\{(.*?)\};", text, re.DOTALL)
    }
    tables = {
        match[1]: [word.strip() for word in match[2].replace("\n", " ").split(",") if word.strip()]
        for match in re.finditer(r"const_s16_arr (\w+)\[56\]\s*=\s*\{(.*?)\};", text, re.DOTALL)
    }
    return arrays, tables


def steps(words: list[int]) -> list[tuple[int, int, int, int]]:
    """The `{type, frames, free, lever}` steps after the twelve word header."""
    found = []
    at = HEADER_WORDS
    while at + STEP_WORDS <= len(words) and words[at] != END_OF_COMMAND:
        kind, frames, free, lever = words[at : at + STEP_WORDS]
        found.append((kind, frames, free, lever))
        at += STEP_WORDS
    return found


def show_lever(lever: int) -> str:
    """`=d` is compared for equality, `~d` is an OR-mask that a diagonal satisfies."""
    return ("=" if lever & EXACT else "~") + LEVER.get(lever & 0xF, hex(lever & 0xF))


def main() -> int:
    root = Path(sys.argv[1]).expanduser()
    wanted = sys.argv[2] if len(sys.argv) > 2 else None  # ruff: ignore[magic-value-comparison] - argv slot
    arrays, tables = load(root)
    gaps: Counter[int] = Counter()
    buttons: Counter[int] = Counter()

    for table, character in zip(TABLES, CHARACTERS, strict=True):
        slots = tables.get(f"{table}_cmd")
        if slots is None:
            continue
        for slot in range(SPECIALS_START, len(slots)):
            if slots[slot] == "dm_cmd_xx":  # An empty slot, shared by everyone who lacks the move.
                continue
            words = arrays[slots[slot]]
            command = steps(words)
            buttons[words[0]] += 1
            gaps.update(frames for index, (kind, frames, _, _) in enumerate(command) if kind == 1 and index)
            if wanted in {None, character}:
                written = " ".join(
                    f"{STEP_TYPES.get(kind, kind)}({show_lever(lever)}, {frames}f)"
                    for kind, frames, _, lever in command
                )
                print(f"{character:8s} {slot:2d} {slots[slot]:12s} button window {words[0]:2d}f  {written}")

    if wanted is None:
        print("\nframes allowed between two steps of a motion:")
        for frames, count in sorted(gaps.items()):
            print(f"  {frames:3d}: {count}")
        print("frames a finished command waits for its button:")
        for frames, count in sorted(buttons.items()):
            print(f"  {frames:3d}: {count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
