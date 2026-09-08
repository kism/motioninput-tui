"""Turn move list notation from the reference FAQs into :class:`MotionSpec`s.

The three FAQs use three different dialects: 3rd Strike and Alpha 3 write
``qcf + P`` and ``Charge b,f + K``, while the Hyper SF2 guide spells everything
out as ``D, DF, F + any Punch`` and ``Charge Back for 2 secs, Forward``. Both
dialects are reduced to a canonical list of direction tokens, which is then
looked up in one table.
"""

import re

from motioninput_tui.engine.motions import MotionKind, MotionSpec
from motioninput_tui.engine.notation import (
    ALL_BUTTONS,
    KICKS,
    PUNCHES,
    Button,
    ButtonRequirement,
    Direction,
)

# Commands describing a follow-up, a stance or something else the trainer has
# no concept of. These are kept in the move list but are not recognisable.
_UNSUPPORTED = re.compile(
    r"\b(during|after|then|while|instead|do nothing|occurs when|knocked|thrown|"
    r"start\b|against a wall|blocking|attacked|near a knife|when armed|"
    r"back-turned|from (?!far\b|afar\b|distance\b)|hold and release|press and hold|get \d)",
)

MULTI_BUTTON = 2

_PARENTHETICAL = re.compile(r"\([^)]*\)")
_STOCKS = re.compile(r"\bx\s*\(?\s*(max\s+stocks?|\d+)\s*\)?\s*(/\s*\d+)?\s*$")
_SECONDS = re.compile(r"for\s+\d+\s+secs?\b")
_QUALIFIERS = re.compile(
    r"\b(when close|when far|from far or up close|from afar|up close|close|far|"
    r"on the left side|on the right side|reversal only|at level \d|"
    r"perform \d+ times|use \d+ times|to cancel|to delay|to charge|to fake|"
    r"any time|rapidly|repeatedly|press|tap|hold|input|the|controller|"
    r"in a full circle or two|full circles?|complete circle)\b",
)

_SHORTHAND: dict[str, str] = {
    "qcf": "d,df,f",
    "qcb": "d,db,b",
    "hcf": "b,db,d,df,f",
    "hcb": "f,df,d,db,b",
}

_WORD_DIRECTIONS: dict[str, str] = {
    "up-back": "ub",
    "up-forward": "uf",
    "down-back": "db",
    "down-forward": "df",
    "upback": "ub",
    "upforward": "uf",
    "downback": "db",
    "downforward": "df",
    "backward": "b",
    "backwards": "b",
    "back": "b",
    "forward": "f",
    "foward": "f",
    "down": "d",
    "up": "u",
    "neutral": "n",
}

_DIRECTION_TOKENS = ("ub", "uf", "db", "df", "b", "f", "d", "u", "n")

_HOLD_DIRECTIONS: dict[str, Direction] = {
    "b": Direction.BACK,
    "f": Direction.FORWARD,
    "d": Direction.DOWN,
    "u": Direction.UP,
    "db": Direction.DOWN_BACK,
    "df": Direction.DOWN_FORWARD,
    "ub": Direction.UP_BACK,
    "uf": Direction.UP_FORWARD,
}

_MOTION_TABLE: dict[tuple[str, ...], MotionKind] = {
    ("d", "df", "f"): MotionKind.QCF,
    ("d", "f"): MotionKind.QCF,
    ("d", "db", "b"): MotionKind.QCB,
    ("d", "b"): MotionKind.QCB,
    ("b", "db", "d", "df", "f"): MotionKind.HCF,
    ("f", "df", "d", "db", "b"): MotionKind.HCB,
    ("f", "d", "df"): MotionKind.DP,
    ("b", "d", "db"): MotionKind.RDP,
    ("db", "d", "df", "f", "uf"): MotionKind.TIGER_KNEE,
    ("d", "df", "f", "uf"): MotionKind.QCF_UF,
    ("b", "db", "d", "df", "f", "uf"): MotionKind.HCF,
    ("d", "df", "f", "d", "df", "f"): MotionKind.QCF_X2,
    ("d", "db", "b", "d", "db", "b"): MotionKind.QCB_X2,
    ("b", "db", "d", "df", "f", "b", "db", "d", "df", "f"): MotionKind.HCF_X2,
    ("f", "df", "d", "db", "b", "f", "df", "d", "db", "b"): MotionKind.HCB_X2,
    ("d", "df", "f", "d", "df"): MotionKind.QCF_DP,
    ("d", "db", "b", "d", "db"): MotionKind.QCB_RDP,
}

_CHARGE_TABLE: dict[tuple[str, ...], MotionKind] = {
    ("b", "f"): MotionKind.CHARGE_BF,
    ("d", "u"): MotionKind.CHARGE_DU,
    ("b", "f", "b", "f"): MotionKind.CHARGE_BFBF,
    ("db", "df", "db", "uf"): MotionKind.CHARGE_DB_UF,
    ("db", "df", "db", "u"): MotionKind.CHARGE_DB_UF,
}

_BUTTON_WORDS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\ball (?:three )?punch(?:es)?\b"), "ppp"),
    (re.compile(r"\ball (?:three )?kicks?\b"), "kkk"),
    (re.compile(r"\bany two punch(?:es)?\b"), "pp"),
    (re.compile(r"\bany two kicks?\b"), "kk"),
    (re.compile(r"\bany punch(?:es)?\b"), "p"),
    (re.compile(r"\bany kicks?\b"), "k"),
    (re.compile(r"\bsame p \+ k\b"), "p+k"),
]

_BUTTON_TOKEN = re.compile(r"\b(lp|mp|hp|lk|mk|hk|ppp|kkk|pp|kk|p|k)\b")

_SPECIFIC_BUTTONS: dict[str, Button] = {button.value.lower(): button for button in Button}


class ParsedCommand:
    """The result of normalising one command string."""

    __slots__ = ("motion", "reason")

    def __init__(self, motion: MotionSpec | None, reason: str = "") -> None:
        """Store the motion, or why there is not one."""
        self.motion = motion
        self.reason = reason


def parse_command(command: str) -> ParsedCommand:
    """Normalise a move list command into a :class:`MotionSpec`."""
    raw = command.strip().lower()
    if not raw:
        return ParsedCommand(None, "empty")
    if _UNSUPPORTED.search(_PARENTHETICAL.sub(" ", raw)):
        return ParsedCommand(None, "conditional or follow-up move")

    text = _strip_noise(raw)
    buttons = _parse_buttons(text)
    if buttons is None:
        return ParsedCommand(None, "no button requirement found")

    kind, hold, reason = _classify(raw, text, buttons)
    if kind is None:
        return ParsedCommand(None, reason)
    return ParsedCommand(MotionSpec(kind, buttons, hold=hold, air=_detect_air(raw), notation=command.strip()))


def _classify(raw: str, text: str, buttons: ButtonRequirement) -> tuple[MotionKind | None, Direction | None, str]:
    """Pick the motion kind for a command whose button requirement is already known."""
    # A 360 that ends in mashing is still a 360, so rotations are checked first.
    rotation = _parse_rotation(text)
    if rotation is not None:
        return rotation, None, ""

    kind, hold, reason = _resolve_directions(raw, text, buttons)
    if kind is not None:
        return kind, hold, ""

    # "Tap P rapidly" on its own is a mash. "qcf,qcf + P, tap P rapidly" is a
    # real motion with a mashable tail for extra hits, and matched just above.
    if "rapid" in raw:
        return MotionKind.MASH, None, ""

    return None, None, reason


def _resolve_directions(
    raw: str, text: str, buttons: ButtonRequirement
) -> tuple[MotionKind | None, Direction | None, str]:
    """Turn the direction tokens of a command into a motion kind."""
    # "Charge Back for 2 secs, Forward" never says the word charge in Hyper SF2.
    charged = "charge" in text or bool(_SECONDS.search(raw))
    tokens = _direction_tokens(text)

    if not tokens:
        if buttons.count < MULTI_BUTTON:
            return None, None, "no directional or multi-button requirement"
        return MotionKind.ANY, None, ""

    kind = (_CHARGE_TABLE if charged else _MOTION_TABLE).get(tuple(tokens))
    if kind is not None:
        return kind, None, ""
    if not charged and len(tokens) == 1 and tokens[0] in _HOLD_DIRECTIONS:
        return MotionKind.HOLD, _HOLD_DIRECTIONS[tokens[0]], ""
    return None, None, f"unrecognised motion {','.join(tokens)!r}"


_AIR_PREFIX = re.compile(r"^\s*in (?:the )?air\b")


def _detect_air(text: str) -> bool:
    """Only an explicit '(air)' marker or an 'In air,' prefix means airborne.

    Notes such as '(can be done in air in SF2 Turbo and up)' describe an
    optional air version of a ground move, so they must not count.
    """
    return bool(re.search(r"\(\s*air\s*\)", text)) or bool(_AIR_PREFIX.match(text))


def _strip_noise(text: str) -> str:
    text = _PARENTHETICAL.sub(" ", text)
    text = text.replace("in air,", " ").replace("in the air,", " ")
    text = _STOCKS.sub(" ", text)
    text = _SECONDS.sub(" ", text)
    text = _QUALIFIERS.sub(" ", text)
    text = text.replace("rotate", " ")
    text = re.sub(r"\bor\b", "/", text)  # "Back or Forward", "MP or HP"
    for word, short in _WORD_DIRECTIONS.items():
        text = re.sub(rf"\b{word}\b", short, text)
    for shorthand, expansion in _SHORTHAND.items():
        text = re.sub(rf"\b{shorthand}\b", expansion, text)
    # Alternatives ("f,d,df / b,d,db") keep only the first option.
    text = re.sub(r"\s+/\s+", " / ", text)
    return re.sub(r"\s+", " ", text).strip(" ,")


def _parse_rotation(text: str) -> MotionKind | None:
    if "720" in text:
        return MotionKind.ROTATE_720
    if "360" in text:
        return MotionKind.ROTATE_360
    return None


def _button_section(text: str) -> str:
    """The tail of the command from the first button token onwards."""
    for pattern, replacement in _BUTTON_WORDS:
        text = pattern.sub(replacement, text)
    match = _BUTTON_TOKEN.search(text)
    if match is None:
        return ""
    return text[match.start() :]


def _parse_buttons(text: str) -> ButtonRequirement | None:
    section = _button_section(text)
    if not section:
        return None

    alternatives = section.split(" / ")
    per_alternative = [
        {_SPECIFIC_BUTTONS[token] for token in _BUTTON_TOKEN.findall(option) if token in _SPECIFIC_BUTTONS}
        for option in alternatives
    ]
    named = [option for option in per_alternative if option]
    if named:
        # "MP or HP" is a choice of one; "LP + LK" needs both at once.
        if len(named) > 1 and all(len(option) == 1 for option in named):
            return ButtonRequirement(frozenset().union(*named), 1)
        return ButtonRequirement(frozenset(named[0]), len(named[0]))

    tokens = _BUTTON_TOKEN.findall(alternatives[0])
    if not tokens:
        return None

    token = tokens[0]
    family = PUNCHES if token.startswith("p") else KICKS
    if token in {"p", "k"}:
        return ButtonRequirement(ALL_BUTTONS if "p+k" in alternatives[0] else family, 1)
    return ButtonRequirement(family, len(token))


_REPEAT = re.compile(r"\bx\s*2\b")


def _direction_tokens(text: str) -> list[str]:
    """Direction tokens appearing before the button requirement."""
    section = _button_section(text)
    head = text[: len(text) - len(section)] if section else text
    if "any direction" in head or "any dir" in head:
        return []
    head = head.replace("+", " ")

    alternatives = [tokens for tokens in (_tokens_in(part) for part in head.split(" / ")) if tokens]
    if not alternatives:
        return []
    # "b / f + PP" means either side works, so there is no direction to hold.
    if len(alternatives) > 1 and all(len(option) == 1 for option in alternatives):
        return []
    # "Jump b / f, d + HP": the choice is only over the first token, so the
    # real requirement is whatever follows it.
    if len(alternatives) == 2 and len(alternatives[0]) == 1 and len(alternatives[1]) > 1:  # ruff: ignore[magic-value-comparison]
        return alternatives[1][1:]

    tokens = alternatives[0]
    if _REPEAT.search(head):  # "D, DF, F x 2" is written out once and repeated
        tokens = [*tokens, *tokens]
    return tokens


def _tokens_in(part: str) -> list[str]:
    return [chunk for chunk in re.split(r"[,\s]+", part.strip()) if chunk in _DIRECTION_TOKENS]
