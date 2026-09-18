"""Turn move list notation from the reference FAQs into :class:`MotionSpec`s.

The three FAQs use three different dialects: 3rd Strike and Alpha 3 write
``qcf + P`` and ``Charge b,f + K``, while the Hyper SF2 guide spells everything
out as ``D, DF, F + any Punch`` and ``Charge Back for 2 secs, Forward``. Both
dialects are reduced to a canonical list of direction tokens, which is then
looked up in one table.
"""

import re
from itertools import pairwise

from motioninput_tui.engine.motions import MotionKind, MotionSpec
from motioninput_tui.engine.notation import (
    ALL_BUTTONS,
    DIRECTION_RING,
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

# "tap P rapidly" after a motion never comes with a count, so assume three taps.
_MASH_DEFAULT = 3

# "rapidly" everywhere, and "repeatedly" in the KoF guides.
_MASHING = re.compile(r"rapid|repeatedly")

# Something the player *may* do after the move, which does not gate it: Elena's
# Healing is a plain qcf,qcf + P and the PP only stops it early. "to cancel" and
# its friends are already noise to _QUALIFIERS; it is the "then" in front of
# them that would otherwise read as a follow-up condition and drop the move.
#
# `then...` with nothing after it is the same idea written as punctuation: the
# ellipsis points at the moves listed underneath, so the input is the head on
# its own. Cammy's Hooligan Combination really is `hcf,uf + P`, and what she
# does out of it is the next few rows of the guide.
_OPTIONAL_TAIL = re.compile(r",?\s*then(?:\s+[a-z+]+\s+to\s+(?:cancel|delay|fake)\b|\s*\.\.\.\s*$)")

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

_SHORTHAND_RUN = re.compile(rf"\b(?:{'|'.join(_SHORTHAND)})(?:\s*,\s*(?:{'|'.join(_SHORTHAND)}))*\b")


def _expand_shorthand(match: re.Match[str]) -> str:
    """Spell out a run of shorthands, sharing the direction two of them meet on.

    KoF's ``qcf,hcb`` is one roll of the stick through
    ``d,df,f,df,d,db,b``: the forward the quarter circle ends on is the one the
    half circle starts from. Expanding each shorthand on its own would ask for
    it twice, which would mean letting go and pressing it again mid-motion.
    ``qcf,qcf`` and ``hcb,hcb`` meet on different directions and are unaffected.
    """
    tokens: list[str] = []
    for name in re.split(r"\s*,\s*", match.group()):
        for token in _SHORTHAND[name].split(","):
            if not tokens or tokens[-1] != token:
                tokens.append(token)
    return ",".join(tokens)


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
    ("d", "df", "f", "uf"): MotionKind.TIGER_KNEE,
    ("b", "db", "d", "df", "f", "uf"): MotionKind.HCF,
    ("d", "df", "f", "d", "df", "f"): MotionKind.QCF_X2,
    ("d", "db", "b", "d", "db", "b"): MotionKind.QCB_X2,
    ("b", "db", "d", "df", "f", "b", "db", "d", "df", "f"): MotionKind.HCF_X2,
    ("f", "df", "d", "db", "b", "f", "df", "d", "db", "b"): MotionKind.HCB_X2,
    ("f", "d", "df", "f", "d", "df"): MotionKind.DP_X2,
    ("d", "df", "f", "d", "df"): MotionKind.QCF_DP,
    ("d", "db", "b", "d", "db"): MotionKind.QCB_RDP,
    ("d", "df", "f", "df", "d", "db", "b"): MotionKind.QCF_HCB,
    ("d", "db", "b", "db", "d", "df", "f"): MotionKind.QCB_HCF,
    ("f", "df", "d", "db", "b", "db", "d", "df", "f"): MotionKind.HCB_HCF,
    ("f", "df", "d", "db", "b", "f"): MotionKind.HCB_F,
    ("f", "df", "d", "db", "b", "db", "d"): MotionKind.HCB_DB_D,
    ("b", "db", "d", "df", "f", "df", "d"): MotionKind.HCF_DF_D,
    ("d", "db", "b", "db", "f"): MotionKind.QCB_DB_F,
    ("f", "b", "db", "d", "df", "f"): MotionKind.F_HCF,
    ("f", "df", "d"): MotionKind.F_DF_D,
    ("b", "db", "d"): MotionKind.B_DB_D,
}

_CHARGE_TABLE: dict[tuple[str, ...], MotionKind] = {
    ("b", "f"): MotionKind.CHARGE_BF,
    ("db", "f"): MotionKind.CHARGE_DB_F,
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


def parse_command(command: str, *, chained: bool = False) -> ParsedCommand:
    """Normalise a move list command into a :class:`MotionSpec`.

    ``chained`` says the move follows on from another, which is what makes a
    bare button an input worth recognising: a chain link is small precisely
    because its parent did the work. Everywhere else a lone button with no
    direction is an ordinary normal, and matching one would make every move
    list a list of things you get by pressing a button.
    """
    raw = _OPTIONAL_TAIL.sub("", command.strip().lower())
    if not raw:
        return ParsedCommand(None, "empty")
    if _UNSUPPORTED.search(_PARENTHETICAL.sub(" ", raw)):
        return ParsedCommand(None, "conditional or follow-up move")

    text = _strip_noise(raw)
    if _is_button_chain(text):
        return ParsedCommand(None, "a chain of presses, which the trainer has no model for")
    buttons = _parse_buttons(text)
    if buttons is None:
        return ParsedCommand(None, "no button requirement found")

    kind, hold, reason = _classify(raw, text, buttons, chained=chained)
    if kind is None:
        return ParsedCommand(None, reason)
    mash, rhythm, mash_button = _follow_through(raw, kind, buttons)
    return ParsedCommand(
        MotionSpec(
            kind,
            buttons,
            hold=hold,
            air=_detect_air(raw),
            mash=mash,
            mash_rhythm=rhythm,
            mash_button=mash_button,
            notation=command.strip(),
        )
    )


_RHYTHM_TAIL = re.compile(r"\btap\s+([pk])((?:\s*,\s*\1\b)+)")


def _follow_through(raw: str, kind: MotionKind, buttons: ButtonRequirement) -> tuple[int, bool, str]:
    """The follow-up phase a motion carries: a rapid mash, or deliberate taps.

    ``qcf,qcf + P, tap P rapidly`` keeps its motion and gains a mash tail; a bare
    ``tap P rapidly`` is already :attr:`MotionKind.MASH` and gets nothing here.
    ``f,d,df + K, tap P,P,P`` is the deliberate-tap variant (``mash_rhythm``);
    the ``p``/``k`` restriction keeps it off ``Tap b,b`` dashes.

    The third field is ``"P"`` / ``"K"`` when the taps are the other button from
    the motion (Sakura Otoshi is ``+ K`` then ``tap P``), else ``""``.
    """
    if kind is MotionKind.MASH:
        return 0, False, ""
    if _MASHING.search(raw):
        return _MASH_DEFAULT, False, ""
    tail = _RHYTHM_TAIL.search(raw)
    if tail is None:
        return 0, False, ""
    button = tail.group(1).upper()
    motion_label = "P" if buttons.label.startswith("P") else "K" if buttons.label.startswith("K") else ""
    return tail.group(2).count(",") + 1, True, "" if button == motion_label else button


def _is_button_chain(text: str) -> bool:
    """Whether a command is buttons pressed one after another, not together.

    A target combo (``HP, HP, HK, HP``) and Akuma's Raging Demon
    (``LP,LP,f,LK,HP``) are sequences of presses, which the engine has no model
    for. Left alone they do not merely fail to match: the commas fall out with
    the rest of the punctuation and what comes back is "press all of these at
    once", a move the game does not have.

    What marks one is a comma with a button on either side of it. Zangief's
    ``Press PPP, move b / f`` has a comma too, but what follows it is the
    direction to spin in, not a second press; and the section having to run
    from the very front of the command is what keeps this off
    ``qcf + P, tap P rapidly``, whose commas come after a real motion.
    """
    section = _button_section(text)
    if not section or len(section) != len(text) or "," not in section:
        return False
    presses = [bool(_BUTTON_TOKEN.search(part)) for part in section.split(",")]
    return any(earlier and later for earlier, later in pairwise(presses))


def _classify(
    raw: str, text: str, buttons: ButtonRequirement, *, chained: bool = False
) -> tuple[MotionKind | None, Direction | None, str]:
    """Pick the motion kind for a command whose button requirement is already known."""
    # A 360 that ends in mashing is still a 360, so rotations are checked first.
    rotation = _parse_rotation(text)
    if rotation is not None:
        return rotation, None, ""

    kind, hold, reason = _resolve_directions(raw, text, buttons, chained=chained)
    if kind is not None:
        return kind, hold, ""

    # "Tap P rapidly" on its own is a mash. "qcf,qcf + P, tap P rapidly" is a
    # real motion with a mashable tail for extra hits, and matched just above.
    if _MASHING.search(raw):
        return MotionKind.MASH, None, ""

    return None, None, reason


def _resolve_directions(
    raw: str, text: str, buttons: ButtonRequirement, *, chained: bool = False
) -> tuple[MotionKind | None, Direction | None, str]:
    """Turn the direction tokens of a command into a motion kind."""
    # "Charge Back for 2 secs, Forward" never says the word charge in Hyper SF2.
    charged = "charge" in text or bool(_SECONDS.search(raw))
    tokens = _direction_tokens(text)

    if not tokens:
        if buttons.count < MULTI_BUTTON and not chained:
            return None, None, "no directional or multi-button requirement"
        return MotionKind.ANY, None, ""

    kind = (_CHARGE_TABLE if charged else _MOTION_TABLE).get(tuple(tokens))
    if kind is not None:
        return kind, None, ""
    if not charged and len(tokens) == 1 and tokens[0] in _HOLD_DIRECTIONS:
        return MotionKind.HOLD, _HOLD_DIRECTIONS[tokens[0]], ""
    if not charged and _is_full_circle(tokens):
        return MotionKind.ROTATE_360, None, ""
    return None, None, f"unrecognised motion {','.join(tokens)!r}"


_AIR_PREFIX = re.compile(r"^\s*in (?:the )?air\b")


def _detect_air(text: str) -> bool:
    """Whether a move can only be done airborne.

    Only an 'In air,' prefix means that. Every guide's own legend spells out
    that the trailing '(air)' marker is the opposite: the move works on the
    ground *or* in the air (Ryu's Tatsumaki, Sakura's Shunpuu Kyaku), so a
    plain ground input has to match it and it must not carry the flag. Notes
    such as '(can be done in air in SF2 Turbo and up)' are the same story.
    """
    return bool(_AIR_PREFIX.match(text))


def _strip_noise(text: str) -> str:
    text = _PARENTHETICAL.sub(" ", text)
    text = text.replace("in air,", " ").replace("in the air,", " ")
    text = _STOCKS.sub(" ", text)
    text = _SECONDS.sub(" ", text)
    text = _QUALIFIERS.sub(" ", text)
    text = text.replace("rotate", " ")
    text = re.sub(r"\bor\b", "/", text)  # "Back or Forward", "MP or HP"
    # A guide may write the same choice tight, "LP/LK/HP/HK". Without the
    # spaces the alternatives below never split, and four buttons to choose
    # from read as four buttons to press at once.
    text = re.sub(r"(?<=[\w])/(?=[\w])", " / ", text)
    for word, short in _WORD_DIRECTIONS.items():
        text = re.sub(rf"\b{word}\b", short, text)
    text = _SHORTHAND_RUN.sub(_expand_shorthand, text)
    # Alternatives ("f,d,df / b,d,db") keep only the first option.
    text = re.sub(r"\s+/\s+", " / ", text)
    return re.sub(r"\s+", " ", text).strip(" ,")


def _parse_rotation(text: str) -> MotionKind | None:
    if "720" in text:
        return MotionKind.ROTATE_720
    if "360" in text:
        return MotionKind.ROTATE_360
    return None


_RING_POSITIONS = {direction.short: index for index, direction in enumerate(DIRECTION_RING)}
FULL_CIRCLE = len(DIRECTION_RING)


def _is_full_circle(tokens: list[str]) -> bool:
    """Whether the tokens walk the eight directions right the way round.

    Not every guide writes a 360 as "360": one that spells the circle out gets
    one here, where :func:`_parse_rotation` only sees the ones that say so.

    Every step has to be the next notch round, the same way throughout, which is
    what keeps this off the long motions that merely have a lot of directions in
    them. A half circle out and back again covers plenty of the ring but doubles
    back, and is not a revolution.
    """
    if len(tokens) != FULL_CIRCLE or any(token not in _RING_POSITIONS for token in tokens):
        return False
    positions = [_RING_POSITIONS[token] for token in tokens]
    steps = {(later - earlier) % FULL_CIRCLE for earlier, later in pairwise(positions)}
    return steps in ({1}, {FULL_CIRCLE - 1})


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
        return _named_requirement(named, alternatives)

    tokens = _BUTTON_TOKEN.findall(alternatives[0])
    if not tokens:
        return None

    token = tokens[0]
    family = PUNCHES if token.startswith("p") else KICKS
    if token in {"p", "k"}:
        return ButtonRequirement(ALL_BUTTONS if "p+k" in alternatives[0] else family, 1)
    return ButtonRequirement(family, len(token))


def _named_requirement(named: list[set[Button]], alternatives: list[str]) -> ButtonRequirement:
    """The requirement of a command whose alternatives name specific buttons."""
    # "MP or HP" is a choice of one; "LP + LK" needs both at once.
    if len(named) > 1 and all(len(option) == 1 for option in named):
        return ButtonRequirement(frozenset().union(*named), 1)
    # A choice between a family and one button, "qcf + P/LK". The family
    # alternative names no specific button, so it is not in `named` at all, and
    # taking the first option alone would leave the move on the one button the
    # guide offered as the alternative.
    if len(alternatives) > 1 and len(named) == 1 and len(named[0]) == 1:
        family = _family_alternatives(alternatives)
        if family:
            return ButtonRequirement(frozenset().union(*named, *family), 1)
    return ButtonRequirement(frozenset(named[0]), len(named[0]))


def _family_alternatives(alternatives: list[str]) -> list[frozenset[Button]]:
    """The whole-family options of a choice: the ``P`` in ``qcf + P/LK``.

    The family has to be the *whole* of its own alternative. A ``K`` sitting
    inside one alongside another button is a follow-up press rather than a
    choice - Guy's ``qcf + LK,K`` is his run and then a kick out of it, not a
    move on any kick.
    """
    families = []
    for option in alternatives:
        tokens = _BUTTON_TOKEN.findall(option)
        if len(tokens) == 1 and tokens[0] in {"p", "k"}:
            families.append(PUNCHES if tokens[0] == "p" else KICKS)
    return families


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
