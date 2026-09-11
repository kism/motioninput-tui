"""How a move's input is written out in the move list and the activation feed.

This is presentation, not engine: :mod:`motioninput_tui.engine.notation` says
what a direction *is*, and this says how to draw one. The live input strip is
deliberately not part of it — what you actually pressed is always arrows, so
there is one reading of the display that never changes.

A motion is written as a series of parts, and each part is either spelled out
as directions or replaced by the glyph the player picked for its family. So the
same dragon punch reads ``→ ↓ ↘``, ``F, D, DF``, ``𑪼`` or ``龍→`` depending on
the two choices involved, and a super that is a quarter circle twice follows
whatever quarter circles are set to. Moves the engine has no directional model
of keep the reference guide's own words.
"""

import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

from .engine.motions import MotionKind
from .engine.notation import Direction

if TYPE_CHECKING:
    from collections.abc import Mapping

    from .engine.motions import MotionSpec
    from .engine.recognizer import RecognisableMove


class Family(StrEnum):
    """A group of motions that share one way of being written."""

    DIRECTIONS = "directions"
    QUARTER = "quarter"
    HALF = "half"
    DRAGON = "dragon"
    ROTATE = "rotate"
    CHARGE = "charge"


FAMILY_NAMES: dict[Family, str] = {
    Family.DIRECTIONS: "Directions",
    Family.QUARTER: "Quarter circles",
    Family.HALF: "Half circles",
    Family.DRAGON: "Dragon punches",
    Family.ROTATE: "Full circles",
    Family.CHARGE: "Charges",
}


@dataclass(frozen=True, slots=True)
class Style:
    """One way of writing the motions in a family.

    Attributes:
        key: What is saved in the config.
        name: What the notation menu calls it.
        glyphs: The writing for each motion kind. A kind that is missing is
            spelled out as directions instead, which is what makes the first
            style of every family the plain one.
        directions: :attr:`Family.DIRECTIONS` only: how to draw each direction.
            A direction that is missing falls back to its arrow.
        separator: :attr:`Family.DIRECTIONS` only: what goes between them.
            Numpad notation runs them together as ``236``, letters want
            ``D, DF, F``, arrows want the space.
    """

    key: str
    name: str
    glyphs: Mapping[MotionKind, str] = field(default_factory=dict)
    directions: Mapping[Direction, str] = field(default_factory=dict)
    separator: str = " "

    def write_direction(self, direction: Direction) -> str:
        """One direction, drawn this way."""
        return self.directions.get(direction, direction.glyph)


_D = Direction
_K = MotionKind

# Nerd font glyphs sit in the private use area, so they are tofu without a
# patched font. The menu previews every style, which is the honest way to find
# out: if the row is a box, that font is not installed.
_NF_QUARTER_FORWARD = "\U000f17bf"  # nf-md-arrow_up_right
_NF_QUARTER_BACK = "\U000f17bd"  # nf-md-arrow_up_left
_NF_HALF_FORWARD = "\U000f17bb"  # nf-md-arrow_u_up_right
_NF_HALF_BACK = "\U000f17b9"  # nf-md-arrow_u_up_left
_NF_DRAGON = "\ueef8"  # nf-fa-dragon


_LETTERS: dict[Direction, str] = {direction: direction.short.upper() for direction in Direction}
_NUMPAD: dict[Direction, str] = {direction: str(int(direction)) for direction in Direction}
_KEYCAPS: dict[Direction, str] = {direction: f"{int(direction)}\ufe0f\u20e3" for direction in Direction}
"""The numpad as keycap emoji, ``2️⃣3️⃣6️⃣``."""

_EMOJI_ARROWS: dict[Direction, str] = {
    _D.DOWN_BACK: "↙️",
    _D.DOWN: "⬇️",
    _D.DOWN_FORWARD: "↘️",
    _D.BACK: "⬅️",
    _D.FORWARD: "➡️",
    _D.UP_BACK: "↖️",
    _D.UP: "⬆️",
    _D.UP_FORWARD: "↗️",
}

# nf-md-numeric_1_box to nf-md-numeric_9_box, which is the numpad in boxes.
_NF_DIGIT_BOXES = (
    "\U000f03a4",
    "\U000f03a7",
    "\U000f03aa",
    "\U000f03ad",
    "\U000f03b1",
    "\U000f03b3",
    "\U000f03b6",
    "\U000f03b9",
    "\U000f03bc",
)
_NERD_NUMPAD: dict[Direction, str] = {direction: _NF_DIGIT_BOXES[int(direction) - 1] for direction in Direction}

_NF_ROTATE = "\U000f1999"  # nf-md-rotate_360
_NF_LEFT_RIGHT = "\U000f0e73"  # nf-md-arrow_left_right
_NF_UP_DOWN = "\U000f0e79"  # nf-md-arrow_up_down


def _beast(glyph: str) -> dict[MotionKind, str]:
    """A dragon punch written as a creature facing the way the motion ends."""
    return {_K.DP: f"{glyph}→", _K.RDP: f"{glyph}←"}


STYLES: dict[Family, tuple[Style, ...]] = {
    Family.DIRECTIONS: (
        Style(key="arrows", name="Arrows"),
        Style(key="letters", name="Letters", directions=_LETTERS, separator=", "),
        Style(key="numpad", name="Numpad", directions=_NUMPAD, separator=""),
        Style(key="emoji", name="Emoji arrows", directions=_EMOJI_ARROWS),
        Style(key="keycaps", name="Emoji numpad", directions=_KEYCAPS, separator=""),
        Style(key="nerd", name="Nerd numpad", directions=_NERD_NUMPAD, separator=""),
    ),
    Family.QUARTER: (
        Style(key="spelled", name="Spelled out"),
        Style(key="elbow", name="Elbow arrows", glyphs={_K.QCF: "⮡", _K.QCB: "⮠"}),
        Style(key="curved", name="Curved arrows", glyphs={_K.QCF: "⮩", _K.QCB: "⮨"}),
        Style(key="ribbon", name="Ribbon arrows", glyphs={_K.QCF: "⮱", _K.QCB: "⮰"}),
        Style(key="return", name="Return arrows", glyphs={_K.QCF: "⮑", _K.QCB: "⮐"}),
        Style(key="nerd", name="Nerd font", glyphs={_K.QCF: _NF_QUARTER_FORWARD, _K.QCB: _NF_QUARTER_BACK}),
        Style(key="emoji", name="Emoji fireball", glyphs={_K.QCF: "🔥→", _K.QCB: "🔥←"}),
    ),
    Family.HALF: (
        Style(key="spelled", name="Spelled out"),
        Style(key="cup", name="Cup", glyphs={_K.HCF: "⋃→", _K.HCB: "⋃←"}),
        Style(key="arc", name="Arc", glyphs={_K.HCF: "◡→", _K.HCB: "◡←"}),
        Style(key="nerd", name="Nerd font", glyphs={_K.HCF: _NF_HALF_FORWARD, _K.HCB: _NF_HALF_BACK}),
        Style(key="emoji", name="Emoji moon", glyphs={_K.HCF: "🌙→", _K.HCB: "🌙←"}),
    ),
    Family.DRAGON: (
        Style(key="spelled", name="Spelled out"),
        Style(key="canadian", name="Canadian Syllabics", glyphs={_K.DP: "𑪼", _K.RDP: "𑪽"}),
        Style(key="turkic", name="Old Turkic", glyphs={_K.DP: "𐰁", _K.RDP: "𐰀"}),
        Style(key="kanji", name="Dragon 龍", glyphs=_beast("龍")),
        Style(key="simplified", name="Dragon 龙", glyphs=_beast("龙")),
        Style(key="japanese", name="Dragon 竜", glyphs=_beast("竜")),
        Style(key="hieroglyph", name="Serpent 𓆈", glyphs=_beast("𓆈")),
        Style(key="nerd", name="Nerd font", glyphs=_beast(_NF_DRAGON)),
        Style(key="emoji", name="Emoji dragon", glyphs=_beast("🐉")),
    ),
    Family.ROTATE: (
        Style(key="spelled", name="Spelled out"),
        Style(key="open", name="Open circles", glyphs={_K.ROTATE_360: "⥁", _K.ROTATE_720: "⥁ ⥁"}),
        Style(key="circle", name="Circle arrows", glyphs={_K.ROTATE_360: "⭮", _K.ROTATE_720: "⭮ ⭮"}),
        Style(
            key="nerd",
            name="Nerd font",
            glyphs={_K.ROTATE_360: _NF_ROTATE, _K.ROTATE_720: f"{_NF_ROTATE} {_NF_ROTATE}"},
        ),
        Style(key="emoji", name="Emoji cyclone", glyphs={_K.ROTATE_360: "🌀", _K.ROTATE_720: "🌀 🌀"}),
    ),
    Family.CHARGE: (
        Style(key="spelled", name="Spelled out"),
        Style(
            key="paired",
            name="Paired arrows",
            glyphs={_K.CHARGE_BF: "⮀", _K.CHARGE_DU: "⮃", _K.CHARGE_BFBF: "⮀ ⮀"},
        ),
        Style(
            key="nerd",
            name="Nerd font",
            glyphs={
                _K.CHARGE_BF: _NF_LEFT_RIGHT,
                _K.CHARGE_DU: _NF_UP_DOWN,
                _K.CHARGE_BFBF: f"{_NF_LEFT_RIGHT} {_NF_LEFT_RIGHT}",
            },
        ),
        Style(
            key="emoji",
            name="Emoji battery",
            glyphs={_K.CHARGE_BF: "🔋→", _K.CHARGE_DU: "🔋↑", _K.CHARGE_BFBF: "🔋→ ← →"},
        ),
    ),
}

_KIND_FAMILY: dict[MotionKind, Family] = {
    _K.QCF: Family.QUARTER,
    _K.QCB: Family.QUARTER,
    _K.HCF: Family.HALF,
    _K.HCB: Family.HALF,
    _K.DP: Family.DRAGON,
    _K.RDP: Family.DRAGON,
    _K.ROTATE_360: Family.ROTATE,
    _K.ROTATE_720: Family.ROTATE,
    _K.CHARGE_BF: Family.CHARGE,
    _K.CHARGE_DU: Family.CHARGE,
    _K.CHARGE_BFBF: Family.CHARGE,
    _K.CHARGE_DB_UF: Family.CHARGE,
    _K.CHARGE_DB_F: Family.CHARGE,
}

# Compound motions borrow their parts' styles rather than having their own, so
# a double quarter circle follows whatever quarter circles are set to.
_PARTS: dict[MotionKind, tuple[MotionKind | Direction, ...]] = {
    _K.QCF_X2: (_K.QCF, _K.QCF),
    _K.QCB_X2: (_K.QCB, _K.QCB),
    _K.HCF_X2: (_K.HCF, _K.HCF),
    _K.HCB_X2: (_K.HCB, _K.HCB),
    _K.QCF_DP: (_K.QCF, _K.DP),
    _K.QCB_RDP: (_K.QCB, _K.RDP),
    _K.QCF_UF: (_K.QCF, _D.UP_FORWARD),
    _K.QCF_HCB: (_K.QCF, _K.HCB),
    _K.QCB_HCF: (_K.QCB, _K.HCF),
    _K.HCB_F: (_K.HCB, _D.FORWARD),
    _K.QCB_DB_F: (_K.QCB, _D.DOWN_BACK, _D.FORWARD),
    _K.F_HCF: (_D.FORWARD, _K.HCF),
}

_SEQUENCES: dict[MotionKind, tuple[Direction, ...]] = {
    _K.QCF: (_D.DOWN, _D.DOWN_FORWARD, _D.FORWARD),
    _K.QCB: (_D.DOWN, _D.DOWN_BACK, _D.BACK),
    _K.HCF: (_D.BACK, _D.DOWN_BACK, _D.DOWN, _D.DOWN_FORWARD, _D.FORWARD),
    _K.HCB: (_D.FORWARD, _D.DOWN_FORWARD, _D.DOWN, _D.DOWN_BACK, _D.BACK),
    _K.DP: (_D.FORWARD, _D.DOWN, _D.DOWN_FORWARD),
    _K.RDP: (_D.BACK, _D.DOWN, _D.DOWN_BACK),
    _K.TIGER_KNEE: (_D.DOWN, _D.DOWN_FORWARD, _D.FORWARD, _D.UP_FORWARD),
    _K.F_DF_D: (_D.FORWARD, _D.DOWN_FORWARD, _D.DOWN),
    _K.B_DB_D: (_D.BACK, _D.DOWN_BACK, _D.DOWN),
}

# A charge is a direction held, then the ones tapped after letting it go.
_CHARGES: dict[MotionKind, tuple[Direction, tuple[Direction, ...]]] = {
    _K.CHARGE_BF: (_D.BACK, (_D.FORWARD,)),
    _K.CHARGE_DU: (_D.DOWN, (_D.UP,)),
    _K.CHARGE_BFBF: (_D.BACK, (_D.FORWARD, _D.BACK, _D.FORWARD)),
    _K.CHARGE_DB_UF: (_D.DOWN_BACK, (_D.DOWN_FORWARD, _D.DOWN_BACK, _D.UP_FORWARD)),
    _K.CHARGE_DB_F: (_D.DOWN_BACK, (_D.FORWARD,)),
}

_ROTATIONS: dict[MotionKind, str] = {_K.ROTATE_360: "360", _K.ROTATE_720: "720"}

_PREVIEWS: dict[Family, tuple[MotionKind, ...]] = {
    Family.QUARTER: (_K.QCF, _K.QCB),
    Family.HALF: (_K.HCF, _K.HCB),
    Family.DRAGON: (_K.DP, _K.RDP),
    Family.ROTATE: (_K.ROTATE_360, _K.ROTATE_720),
    Family.CHARGE: (_K.CHARGE_BF, _K.CHARGE_DU),
}

_SAMPLE_DIRECTIONS: tuple[Direction, ...] = (_D.DOWN, _D.DOWN_FORWARD, _D.FORWARD)
"""What the directions family previews, since it has no motion of its own."""

PART_GAP = "  "
"""Between the parts of a compound motion, so the halves of a super read apart."""

REPEATED = 2
"""Parts in a motion that is just another one done twice."""

REPEAT_MARK = "×2"
"""A motion done twice is marked rather than written out twice, which is both
shorter and how the guides put it."""

# Stock counts and parenthetical asides, dropped from a guide's own wording.
_NOISE = re.compile(r"\s*(\(.*?\)|x\s*\(?(max stocks?|\d)\)?.*)\s*$")


def plain_command(command: str) -> str:
    """A reference command with the asides trimmed off it."""
    return _NOISE.sub("", command).strip().removeprefix("Press ").strip()


@dataclass(frozen=True, slots=True)
class Notation:
    """The style chosen for each family, and the writing that follows from it."""

    choices: Mapping[str, str] = field(default_factory=dict)
    """Family key to style key. Anything missing or unknown falls back to the
    family's first style, so a part-filled config still writes everything."""

    def style(self, family: Family) -> Style:
        """The style in force for ``family``."""
        wanted = self.choices.get(family.value)
        for style in STYLES[family]:
            if style.key == wanted:
                return style
        return STYLES[family][0]

    def with_style(self, family: Family, style: Style) -> Notation:
        """The same choices with one family changed, for previewing it."""
        return Notation({**self.choices, family.value: style.key})

    def write_move(self, move: RecognisableMove) -> str:
        """How this move's input is written.

        A move the engine has no directional model of keeps the guide's own
        words: there is nothing to draw, and the wording is all the player has.
        """
        spec = move.motion
        if spec is None or spec.kind is MotionKind.ANY:
            return plain_command(move.command)
        return self.write(spec)

    def write(self, spec: MotionSpec) -> str:
        """How this input requirement is written, buttons included."""
        buttons = spec.buttons.label
        if spec.kind is MotionKind.MASH:
            return f"mash {buttons}"
        motion = self._motion(spec)
        text = f"{motion} + {buttons}" if motion else buttons
        if spec.air:
            text = f"{text} (air)"
        if spec.mash:
            tail = spec.follow_up_label
            text = f"{text}, tap {tail}×{spec.mash}" if spec.mash_rhythm else f"{text}, mash {tail}"
        return text

    def preview(self, family: Family, style: Style) -> str:
        """What ``style`` would look like, with every other family left alone."""
        trial = self.with_style(family, style)
        if family is Family.DIRECTIONS:
            return trial.directions(_SAMPLE_DIRECTIONS)
        return "   ".join(trial.write_part(kind) for kind in _PREVIEWS[family])

    def directions(self, sequence: tuple[Direction, ...]) -> str:
        """A run of directions in the chosen direction style."""
        style = self.style(Family.DIRECTIONS)
        return style.separator.join(style.write_direction(direction) for direction in sequence)

    def _motion(self, spec: MotionSpec) -> str:
        """The directional half of a requirement, without the buttons."""
        if spec.kind is MotionKind.HOLD:
            return "" if spec.hold is None else self.directions((spec.hold,))
        if spec.kind is MotionKind.ANY:
            return ""
        parts = _PARTS.get(spec.kind, (spec.kind,))
        written = [self.write_part(part) for part in parts]
        if len(written) == REPEATED and written[0] == written[1]:
            return f"{written[0]} {REPEAT_MARK}"
        return PART_GAP.join(written)

    def write_part(self, part: MotionKind | Direction) -> str:
        """One part of a motion: a glyph if the player picked one, else spelled out."""
        if isinstance(part, Direction):
            return self.directions((part,))
        family = _KIND_FAMILY.get(part)
        if family is not None:
            glyph = self.style(family).glyphs.get(part)
            if glyph:
                return glyph
        return self._spelled(part)

    def _spelled(self, kind: MotionKind) -> str:
        """A motion written out as the directions it is made of."""
        charge = _CHARGES.get(kind)
        if charge is not None:
            hold, release = charge
            return f"[{self.directions((hold,))}] {self.directions(release)}"
        rotation = _ROTATIONS.get(kind)
        if rotation is not None:
            return rotation
        return self.directions(_SEQUENCES.get(kind, ()))


DEFAULT = Notation()
"""Arrows, everything spelled out. What the trainer looks like unchanged."""
