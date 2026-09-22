"""Shared helpers for the reference FAQ parsers."""

import re
import unicodedata
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING

from motioninput_tui.engine.motions import MotionKind
from motioninput_tui.engine.notation import ALL_BUTTONS, KICKS, PUNCHES, Button, ButtonRequirement
from motioninput_tui.games.models import Category, Character, Move

from .normalise import parse_command

if TYPE_CHECKING:
    from collections.abc import Sequence

SUPER_KINDS = frozenset(
    {
        MotionKind.QCF_X2,
        MotionKind.QCB_X2,
        MotionKind.HCF_X2,
        MotionKind.HCB_X2,
        MotionKind.DP_X2,
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


def build_move(  # ruff: ignore[too-many-arguments] - the fields of one move row, and folding them into a struct would touch every parser
    name: str,
    command: str,
    report: ParseReport,
    character: str,
    category: str | None = None,
    *,
    follows: str = "",
) -> Move:
    """Normalise one move list entry.

    ``follows`` names the move this one chains from, and is also what tells
    :func:`parse_command` that a bare button is a real input here.
    """
    parsed = parse_command(command, chained=bool(follows))
    if parsed.motion is None:
        report.note(character, name, parsed.reason)
        resolved = category or Category.OTHER
    else:
        resolved = category or categorise(name, parsed.motion.kind, parsed.motion.buttons.count)
    return Move(name=name, command=command, category=resolved, motion=parsed.motion, follows=follows)


def _dedupe(moves: list[Move]) -> list[Move]:
    """Drop repeats. Alpha 3 lists per-ISM variants of the same move."""
    seen: set[tuple[str, str, str, str]] = set()
    unique = []
    for move in moves:
        # The parent is part of the signature: a guide can hang the same
        # follow-up off two different parents, and those are two moves. So is
        # the button, or Guile's two Knees - one on MK and one on LK, the same
        # move in different versions of SF2 - would come out as one.
        signature = (
            move.name,
            move.motion.kind if move.motion else move.command,
            move.motion.buttons.label if move.motion else "",
            move.follows,
        )
        if signature in seen:
            continue
        seen.add(signature)
        unique.append(move)
    return unique


def _inherit_chain_categories(moves: list[Move]) -> list[Move]:
    """Put a chain link in the same section of the move list as its parent.

    A link's own input is usually a bare button, which :func:`categorise` can
    only call ``other``, so a guide that does not say outright which section a
    move belongs to leaves Akuma's three Hyakki Gou moves filed away from the
    Hyakki Shuu they come out of. Taking the parent's section is the answer:
    a link in a special's string is part of that special.

    Only a move the parser had nothing better for is changed, so a guide that
    does say - Martial Masters by its headings, KoF by its boxes - keeps what
    it said. Parents come before their links, so one pass carries a category
    the length of a string.
    """
    known: dict[str, str] = {}
    inherited: list[Move] = []
    for move in moves:
        parent = known.get(move.follows) if move.follows and move.category == Category.OTHER else None
        resolved = replace(move, category=parent) if parent else move
        known[resolved.name] = resolved.category
        inherited.append(resolved)
    return inherited


def finish_character(name: str, title: str, moves: list[Move], report: ParseReport) -> Character | None:
    """Wrap up a parsed character, dropping ones with nothing usable."""
    if not moves:
        return None
    moves = _inherit_chain_categories(_dedupe(moves))
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


def narrow_buttons(
    requirement: ButtonRequirement, punches: frozenset[Button], kicks: frozenset[Button]
) -> ButtonRequirement:
    """A requirement with the strengths a four-button panel does not have dropped.

    ``normalise`` reads one dialect, the Street Fighter six, so "any punch"
    comes back as three buttons. On a panel with two of each it is reachable on
    two, and a move asking for either family is reachable on four. The specific
    buttons a command names are left alone: a guide written in ``LP``/``HK`` is
    already naming buttons this panel has.
    """
    count = requirement.count
    if requirement.allowed == PUNCHES:
        return ButtonRequirement(punches, count, "P" * count)
    if requirement.allowed == KICKS:
        return ButtonRequirement(kicks, count, "K" * count)
    if requirement.allowed == ALL_BUTTONS:
        return ButtonRequirement(punches | kicks, count, "any button")
    return requirement


_TRAILING_PARENT = re.compile(r"^(.*?)[,\s]+\b(?:during|after)\b\s+(.+?)\s*$", re.IGNORECASE)
"""The Street Fighter guides' chain: this half's input, then the move it comes
out of. ``Press P during Ducking``, ``b / f + P after Head Press``. The Neo Geo
guides write the two the other way round, which is
:func:`neogeo.split_parent`."""

_THEN_PARENT = re.compile(r"^(.*?),\s*\bthen\b\s+(.+?)\s*$", re.IGNORECASE)
"""The same guides' other way of writing one, where the parent is not named at
all but spelled out as its own command again: Akuma's dive is ``qcf,uf + P``
and each of the three moves off it is ``qcf,uf + P, then <something>``."""

_PARENT_ASIDE = re.compile(r"\s*\([^)]*\)\s*$")


def split_follow_on(command: str, so_far: Sequence[Move]) -> tuple[str, str]:
    """A chain link's own input and the move it follows, or ``("", "")``.

    Two shapes, because the Street Fighter guides use both. Either the parent
    is named on the end (``Press P during Ducking``), or it is written out as
    its own command again with this half after it (``qcf,uf + P, then press
    P``). Both are only taken when they point at a move the character already
    has, so prose the trainer cannot model - ``after H.C.``, ``during standing
    MK`` - leaves the move struck through as it was rather than linked to
    nothing.

    A third way is punctuation alone: a command opening with ``...`` continues
    the move above it, which is how 3rd Strike's guide writes Akuma's dive.

    The ``then`` shape needs the head to be *exactly* another move's command,
    which is what tells Akuma's three Hyakki Gou moves (his Hyakki Shuu dive
    really is a move of its own) from Rufus's Messiah Kick, whose ``qcf + K,
    then K`` is one move and an extra press rather than a chain.

    Every command carrying ``during``, ``after`` or ``then`` is already
    untrainable, since ``normalise._UNSUPPORTED`` rejects all three, so nothing
    that currently comes out can be changed by this.
    """
    return (
        _named_parent(command, so_far)
        or _command_parent(command, so_far)
        or _previous_parent(command, so_far)
        or ("", "")
    )


def _named_parent(command: str, so_far: Sequence[Move]) -> tuple[str, str] | None:
    """``<input> during <Parent>``, where the parent is named on the end.

    The shortest candidate wins, being the one the trailing text accounts for
    most of.
    """
    found = _TRAILING_PARENT.match(command.strip())
    if found is None:
        return None
    own = found.group(1).strip().rstrip(",")
    parent = _PARENT_ASIDE.sub("", found.group(2).strip()).rstrip(".").strip()
    if not own or not parent:
        return None
    lowered = parent.lower()
    named = [
        move.name for move in so_far if move.name and (move.name.lower() in lowered or lowered in move.name.lower())
    ]
    if not named:
        return None
    return own, min(named, key=len)


def _command_parent(command: str, so_far: Sequence[Move]) -> tuple[str, str] | None:
    """``<parent's own command>, then <input>``.

    Matched on the command rather than a name, and it has to be the whole of
    one: a head that merely starts like another move's command is this move's
    own input with a tail the engine has no model for, not a link.
    """
    found = _THEN_PARENT.match(command.strip())
    if found is None:
        return None
    head, own = _squash(found.group(1)), found.group(2).strip()
    if not head or not own:
        return None
    parent = next((move.name for move in so_far if move.name and _squash(move.command) == head), "")
    if not parent:
        return None
    return own, parent


_ELLIPSIS = "..."


def _previous_parent(command: str, so_far: Sequence[Move]) -> tuple[str, str] | None:
    """``...press P``, which continues whatever was listed last.

    The parent is the most recent move that does not itself open with the
    ellipsis, because a run of them all come out of the one move above the run
    rather than each out of the one before it: Akuma's Gou Shou and Gou Jin are
    both things to do out of the Hyakki Shuu, not out of each other.
    """
    stripped = command.strip()
    if not stripped.startswith(_ELLIPSIS):
        return None
    own = stripped.removeprefix(_ELLIPSIS).strip()
    parent = next(
        (move.name for move in reversed(so_far) if move.name and not move.command.strip().startswith(_ELLIPSIS)),
        "",
    )
    if not own or not parent:
        return None
    return own, parent


def _squash(text: str) -> str:
    """One command in the form two of them are compared in."""
    return MULTI_SPACE.sub(" ", text.strip().lower())
