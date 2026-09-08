"""Game, character and move data models."""

from dataclasses import dataclass, field
from enum import StrEnum

from motioninput_tui.controls.buttons import STREET_FIGHTER, ButtonSet
from motioninput_tui.engine.motions import MotionSpec
from motioninput_tui.engine.ruleset import Ruleset


class Category(StrEnum):
    """Roughly what sort of move this is, used for grouping and colour."""

    SUPER = "super"
    SPECIAL = "special"
    COMMAND = "command"
    THROW = "throw"
    MOVEMENT = "movement"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class Move:
    """A single move from a character's move list."""

    name: str
    command: str
    category: str = Category.OTHER
    motion: MotionSpec | None = None
    notes: str = ""

    @property
    def trainable(self) -> bool:
        """Whether the engine can recognise this move."""
        return self.motion is not None

    def to_dict(self) -> dict[str, object]:
        """Serialise for the generated game data files."""
        data: dict[str, object] = {"name": self.name, "command": self.command, "category": self.category}
        if self.motion is not None:
            data["motion"] = self.motion.to_dict()
        if self.notes:
            data["notes"] = self.notes
        return data

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> Move:
        """Rebuild from a generated game data file."""
        motion = raw.get("motion")
        return cls(
            name=str(raw["name"]),
            command=str(raw["command"]),
            category=str(raw.get("category", Category.OTHER)),
            motion=MotionSpec.from_dict(motion) if motion else None,  # ty: ignore[invalid-argument-type]
            notes=str(raw.get("notes", "")),
        )


@dataclass(frozen=True, slots=True)
class Character:
    """A playable character and their move list."""

    key: str
    name: str
    title: str = ""
    moves: tuple[Move, ...] = ()

    @property
    def trainable_moves(self) -> tuple[Move, ...]:
        """Moves the engine can recognise."""
        return tuple(move for move in self.moves if move.trainable)

    def to_dict(self) -> dict[str, object]:
        """Serialise for the generated game data files."""
        return {
            "key": self.key,
            "name": self.name,
            "title": self.title,
            "moves": [move.to_dict() for move in self.moves],
        }

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> Character:
        """Rebuild from a generated game data file."""
        moves = raw.get("moves", [])
        return cls(
            key=str(raw["key"]),
            name=str(raw["name"]),
            title=str(raw.get("title", "")),
            moves=tuple(Move.from_dict(move) for move in moves),  # ty: ignore[not-iterable]
        )


@dataclass(frozen=True, slots=True)
class Game:
    """A game, its input ruleset and its roster."""

    key: str
    name: str
    short_name: str
    ruleset: Ruleset = field(default_factory=Ruleset)
    buttons: ButtonSet = STREET_FIGHTER
    """The panel it is played on. See :mod:`motioninput_tui.controls.buttons`."""
    characters: tuple[Character, ...] = ()
    notes: tuple[str, ...] = ()
    source: str = ""

    def character(self, key: str) -> Character:
        """Look up a character by key or (case-insensitive) name."""
        wanted = key.strip().lower()
        for candidate in self.characters:
            if candidate.key == wanted or candidate.name.lower() == wanted:
                return candidate
        known = ", ".join(candidate.key for candidate in self.characters)
        message = f"Unknown character {key!r} in {self.short_name}. Known: {known}"
        raise KeyError(message)
