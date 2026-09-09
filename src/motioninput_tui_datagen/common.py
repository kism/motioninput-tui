"""Shared helpers for the reference FAQ parsers."""

import re
import unicodedata
from dataclasses import dataclass, field, replace

from motioninput_tui.engine.motions import MotionKind
from motioninput_tui.games.models import Category, Character, Move

from .normalise import parse_command

SUPER_KINDS = frozenset(
    {
        MotionKind.QCF_X2,
        MotionKind.QCB_X2,
        MotionKind.HCF_X2,
        MotionKind.HCB_X2,
        MotionKind.QCF_DP,
        MotionKind.QCB_RDP,
        MotionKind.CHARGE_BFBF,
        MotionKind.CHARGE_DB_UF,
        MotionKind.ROTATE_720,
    }
)

MULTI_BUTTON = 2

DASHED = re.compile(r"^[\s|+-]*[-]{10,}[\s|+-]*$")
MULTI_SPACE = re.compile(r"\s{2,}")


@dataclass
class ParseReport:
    """Counts of what a parser managed to make sense of."""

    characters: int = 0
    moves: int = 0
    trainable: int = 0
    skipped: list[str] = field(default_factory=list)

    def note(self, character: str, move: str, reason: str) -> None:
        """Record a move the normaliser could not turn into a motion."""
        self.skipped.append(f"{character}: {move} ({reason})")

    def summary(self) -> str:
        """One line describing the parse."""
        pct = (self.trainable / self.moves * 100) if self.moves else 0
        return f"{self.characters} characters, {self.moves} moves, {self.trainable} trainable ({pct:.0f}%)"


def character_key(name: str) -> str:
    """A stable, url-ish key for a character name."""
    folded = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", folded.lower()).strip("-")


def categorise(move_name: str, kind: MotionKind | None, button_count: int) -> str:
    """Best guess at what sort of move this is."""
    if kind is None:
        return Category.OTHER
    if kind in SUPER_KINDS:
        return Category.SUPER
    if kind is MotionKind.HOLD:
        return Category.COMMAND
    if kind is MotionKind.ANY:
        # Two buttons at once with no direction is a throw or a taunt.
        return Category.THROW if button_count >= MULTI_BUTTON else Category.OTHER
    named_throw = any(word in move_name.lower() for word in ("throw", "nage"))
    return Category.THROW if named_throw else Category.SPECIAL


def super_tail(groups: list[list[Move]]) -> list[Move]:
    """Flatten blank-line-delimited move groups, tagging the last one as supers.

    Both KoF guides list a character's moves in a fixed order - throws, command
    attacks, special moves, then the DMs and SDMs - with the DM/SDM block set
    off by its own blank line and nothing else in the guide marking a super.
    So that trailing group is taken as the supers: it is the one reliable
    signal, and it tells Athena's ``632146+AC`` PSYCHIC 9 (a DM) apart from
    Goro's ``632146+P`` Tenchi Gaeshi (a command grab) where the motion cannot.

    A lone group is left alone - a character with no separate DM block would
    otherwise read as entirely supers.
    """
    real = [group for group in groups if group]
    if len(real) > 1:
        real[-1] = [replace(move, category=Category.SUPER) for move in real[-1]]
    return [move for group in real for move in group]


def build_move(name: str, command: str, report: ParseReport, character: str, category: str | None = None) -> Move:
    """Normalise one move list entry."""
    parsed = parse_command(command)
    if parsed.motion is None:
        report.note(character, name, parsed.reason)
        resolved = category or Category.OTHER
    else:
        resolved = category or categorise(name, parsed.motion.kind, parsed.motion.buttons.count)
    return Move(name=name, command=command, category=resolved, motion=parsed.motion)


def _dedupe(moves: list[Move]) -> list[Move]:
    """Drop repeats. Alpha 3 lists per-ISM variants of the same move."""
    seen: set[tuple[str, str]] = set()
    unique = []
    for move in moves:
        signature = (move.name, move.motion.kind if move.motion else move.command)
        if signature in seen:
            continue
        seen.add(signature)
        unique.append(move)
    return unique


def finish_character(name: str, title: str, moves: list[Move], report: ParseReport) -> Character | None:
    """Wrap up a parsed character, dropping ones with nothing usable."""
    if not moves:
        return None
    moves = _dedupe(moves)
    report.characters += 1
    report.moves += len(moves)
    report.trainable += sum(1 for move in moves if move.trainable)
    display = name.title() if name.isupper() else name
    return Character(key=character_key(name), name=display, title=title, moves=tuple(moves))


def split_name_command(text: str) -> tuple[str, str] | None:
    """Split a fixed-width 'Name    command' move line."""
    parts = MULTI_SPACE.split(text.strip(), maxsplit=1)
    if len(parts) != 2:  # ruff: ignore[magic-value-comparison] - need exactly a name and a command
        return None
    name, command = parts[0].strip(), parts[1].strip()
    if not name or not command:
        return None
    return name, command
