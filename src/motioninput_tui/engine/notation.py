"""Fighting game input notation.

Directions use numpad notation, from the perspective of a player on the left
side of the screen (so 6 is forward/towards the opponent, 4 is back):

    7 8 9
    4 5 6
    1 2 3
"""

from dataclasses import dataclass
from enum import IntEnum, StrEnum


class Direction(IntEnum):
    """A joystick/keyboard direction in numpad notation."""

    DOWN_BACK = 1
    DOWN = 2
    DOWN_FORWARD = 3
    BACK = 4
    NEUTRAL = 5
    FORWARD = 6
    UP_BACK = 7
    UP = 8
    UP_FORWARD = 9

    @property
    def glyph(self) -> str:
        """A single character arrow for this direction."""
        return _DIRECTION_GLYPHS[self]

    @property
    def short(self) -> str:
        """The conventional short name, e.g. 'df'."""
        return _DIRECTION_SHORT[self]


_DIRECTION_GLYPHS: dict[Direction, str] = {
    Direction.DOWN_BACK: "↙",
    Direction.DOWN: "↓",
    Direction.DOWN_FORWARD: "↘",
    Direction.BACK: "←",
    Direction.NEUTRAL: "·",
    Direction.FORWARD: "→",
    Direction.UP_BACK: "↖",
    Direction.UP: "↑",
    Direction.UP_FORWARD: "↗",
}

_DIRECTION_SHORT: dict[Direction, str] = {
    Direction.DOWN_BACK: "db",
    Direction.DOWN: "d",
    Direction.DOWN_FORWARD: "df",
    Direction.BACK: "b",
    Direction.NEUTRAL: "n",
    Direction.FORWARD: "f",
    Direction.UP_BACK: "ub",
    Direction.UP: "u",
    Direction.UP_FORWARD: "uf",
}

DOWN_DIRECTIONS = frozenset({Direction.DOWN_BACK, Direction.DOWN, Direction.DOWN_FORWARD})
UP_DIRECTIONS = frozenset({Direction.UP_BACK, Direction.UP, Direction.UP_FORWARD})
BACK_DIRECTIONS = frozenset({Direction.DOWN_BACK, Direction.BACK, Direction.UP_BACK})
FORWARD_DIRECTIONS = frozenset({Direction.DOWN_FORWARD, Direction.FORWARD, Direction.UP_FORWARD})

# Clockwise ring of the eight non-neutral directions, used for rotation detection.
DIRECTION_RING: tuple[Direction, ...] = (
    Direction.FORWARD,
    Direction.DOWN_FORWARD,
    Direction.DOWN,
    Direction.DOWN_BACK,
    Direction.BACK,
    Direction.UP_BACK,
    Direction.UP,
    Direction.UP_FORWARD,
)


# Keyed by (up, down, left, right) once opposing inputs have been cleaned.
_AXES_TO_DIRECTION: dict[tuple[bool, bool, bool, bool], Direction] = {
    (True, False, True, False): Direction.UP_BACK,
    (True, False, False, True): Direction.UP_FORWARD,
    (True, False, False, False): Direction.UP,
    (False, True, True, False): Direction.DOWN_BACK,
    (False, True, False, True): Direction.DOWN_FORWARD,
    (False, True, False, False): Direction.DOWN,
    (False, False, True, False): Direction.BACK,
    (False, False, False, True): Direction.FORWARD,
    (False, False, False, False): Direction.NEUTRAL,
}


def direction_from_axes(*, left: bool, right: bool, down: bool, up: bool, last_horizontal: str = "") -> Direction:
    """Resolve four cardinal holds into a single direction.

    Simultaneous opposite cardinals are cleaned the way a modern hitbox does:
    the newer horizontal input wins, and up beats down. Last-input priority
    matters here rather than being a stylistic choice, because a terminal
    cannot see the player let go of back as they press forward, so left and
    right are routinely held at once during a perfectly ordinary motion.
    """
    if left and right:
        left = last_horizontal == "left"
        right = last_horizontal == "right"
    if down and up:
        down = False
    return _AXES_TO_DIRECTION[up, down, left, right]


class Button(StrEnum):
    """An attack button, from any game's button set.

    The six Street Fighter ones come first because the rosters are written in
    them; the rest exist so a layout can be laid out for another game's panel.
    See :mod:`motioninput_tui.controls.buttons` for which set uses which.
    """

    LP = "LP"
    MP = "MP"
    HP = "HP"
    LK = "LK"
    MK = "MK"
    HK = "HK"
    BL = "BL"
    """Mortal Kombat's block, the fifth button."""
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    SQUARE = "□"
    TRIANGLE = "△"
    CROSS = "✕"
    CIRCLE = "○"
    B1 = "1"
    B2 = "2"
    B3 = "3"
    B4 = "4"
    B5 = "5"
    B6 = "6"
    B7 = "7"
    B8 = "8"


PUNCHES = frozenset({Button.LP, Button.MP, Button.HP})
KICKS = frozenset({Button.LK, Button.MK, Button.HK})
ALL_BUTTONS = PUNCHES | KICKS
"""Every button a *roster* can ask for. The generated data is Street Fighter,
so this is the six, not every member of the enum: widening it would change what
``any button`` means in the move lists."""

BUTTON_ORDER: tuple[Button, ...] = (Button.LP, Button.MP, Button.HP, Button.LK, Button.MK, Button.HK)
"""The six the gamepad rebind screen offers, in panel order."""


@dataclass(frozen=True, slots=True, repr=False)
class ButtonRequirement:
    """Which button(s) a move needs, and how many at once.

    ``allowed`` is the set of buttons that satisfy the requirement and ``count``
    is how many distinct ones must be pressed together. ``qcf + P`` is
    ``allowed=PUNCHES, count=1``; ``PP`` is ``allowed=PUNCHES, count=2``.

    Frozen so that the :class:`~.motions.MotionSpec` holding it compares and
    hashes by value like every other model in here.
    """

    allowed: frozenset[Button]
    count: int = 1
    label: str = ""
    """How the requirement is written. Derived from the other two when empty."""

    def __post_init__(self) -> None:
        """Fill in the label when the caller did not give one."""
        if not self.label:
            object.__setattr__(self, "label", _default_label(self.allowed, self.count))

    def __repr__(self) -> str:
        """Debug representation."""
        return f"ButtonRequirement({self.label})"

    def to_dict(self) -> dict[str, object]:
        """Serialise for the generated game data files."""
        return {"allowed": sorted(b.value for b in self.allowed), "count": self.count, "label": self.label}

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> ButtonRequirement:
        """Rebuild from a generated game data file."""
        allowed = frozenset(Button(value) for value in raw["allowed"])  # ty: ignore[not-iterable]
        return cls(allowed, int(raw["count"]), str(raw.get("label", "")))  # ty: ignore[invalid-argument-type]


def _default_label(allowed: frozenset[Button], count: int) -> str:
    if allowed == PUNCHES:
        return "P" * count
    if allowed == KICKS:
        return "K" * count
    if allowed == ALL_BUTTONS:
        return "any button"
    names = [b.value for b in BUTTON_ORDER if b in allowed]
    # Needing every listed button reads as "LP+LK"; a choice reads as "MP/HP".
    return ("+" if count >= len(names) else "/").join(names)


ANY_PUNCH = ButtonRequirement(PUNCHES, 1)
ANY_KICK = ButtonRequirement(KICKS, 1)
