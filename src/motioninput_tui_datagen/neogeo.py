"""The KoF guides' notation, and the Neo Geo's four-button panel.

``normalise`` reads one dialect, the Street Fighter six, so an SNK guide's
commands are translated into it for parsing and the resulting button
requirement is mapped back here. The recogniser matches ``Button`` identity,
not punch/kick family, so without this every KoF move would want an SF button
the Neo Geo layout never produces.

Shared by the KoF '98 and KoF 2001 parsers. Both guides are by Ice Queen Zero
and write commands the same way, so :func:`to_shorthand` and :func:`unmodelled`
serve both; only the surrounding page layout differs, which is what is left in
each parser.
"""

import re
from dataclasses import replace
from typing import TYPE_CHECKING

from motioninput_tui.engine.notation import ALL_BUTTONS, KICKS, PUNCHES, Button, ButtonRequirement

if TYPE_CHECKING:
    from collections.abc import Sequence

    from motioninput_tui.engine.motions import MotionSpec
    from motioninput_tui.games.models import Move as MoveName

NEO_PUNCHES = frozenset({Button.A, Button.C})
NEO_KICKS = frozenset({Button.B, Button.D})

_TO_NEO = {
    Button.LP: Button.A,
    Button.MP: Button.A,
    Button.HP: Button.C,
    Button.LK: Button.B,
    Button.MK: Button.B,
    Button.HK: Button.D,
}
_NEO_ORDER = (Button.A, Button.B, Button.C, Button.D)

TO_SHORTHAND = {"A": "LP", "B": "LK", "C": "HP", "D": "HK", "P": "any punch", "K": "any kick"}
"""Neo Geo button letters in the dialect ``normalise`` reads. A and B are the
light punch and kick, C and D the heavy pair."""


def to_neo_panel(motion: MotionSpec, command: str) -> MotionSpec:
    """Put a motion's button requirement back onto the Neo Geo's A B C D."""
    return replace(motion, buttons=neo_buttons(motion.buttons), notation=command.strip())


def neo_buttons(requirement: ButtonRequirement) -> ButtonRequirement:
    """The same requirement expressed in Neo Geo buttons."""
    count = requirement.count
    if requirement.allowed == PUNCHES:
        return ButtonRequirement(NEO_PUNCHES, count, "P" * count)
    if requirement.allowed == KICKS:
        return ButtonRequirement(NEO_KICKS, count, "K" * count)
    if requirement.allowed == ALL_BUTTONS:
        return ButtonRequirement(NEO_PUNCHES | NEO_KICKS, count, "any button")
    mapped = frozenset(_TO_NEO.get(button, button) for button in requirement.allowed)
    names = [button.value for button in _NEO_ORDER if button in mapped]
    return ButtonRequirement(mapped, count, ("+" if count >= len(names) else "/").join(names))


_REPEATED = re.compile(r"\(([^()]+)\)\s*x\s*2")
"""``(d, df, f)x2``, expanded here because ``normalise`` reads parentheses as
asides and would drop the motion along with them."""

_CHOICE = r"\s*(?:,\s*or|,|or)\s*"
"""How the options of one button clause are told apart. Samurai Shodown II
writes the longer ones as a list rather than a string of ``or``s, ``+ B, D, AB,
or CD``, so a comma separates two options and the ``, or`` that ends the list
has to be read as one separator rather than two."""

_BUTTONS = re.compile(rf"\+\s*([ABCDPK]{{1,4}}(?:{_CHOICE}[ABCDPK]{{1,4}})*)(?![A-Za-z])")
"""The buttons a command asks for: letters pressed together (``AB``), and the
choices between them the guides write out. Every part of a choice has to be
translated here -- left to ``normalise``, an untranslated ``B`` is not a button
token at all and the move silently narrows to the first option."""

_SPLIT_CHOICE = re.compile(_CHOICE)

_MASHED = re.compile(r"^\s*([ABCDPK]{1,4})(?=\s+(?:rapidly|repeatedly)\b)")
"""``C rapidly``: a mash, whose button has no ``+`` in front of it for
:data:`_BUTTONS` to find."""

_DIRECTION = r"(?:ub|uf|db|df|[bfdun])"
_CHARGED = re.compile(rf"\b({_DIRECTION})~({_DIRECTION})\b")
"""The guides' charge notation, ``d~u`` for "hold down briefly then press up".
The word boundary keeps it off move names -- May Lee has a ``Cho~p!``."""

_TRAILING_AIR = re.compile(r",?\s*\bin (?:the )?air\s*$", re.IGNORECASE)
"""The air requirement sometimes comes last (``d + C in air``) where
``normalise`` only reads it as a leading ``In air,`` prefix."""

_QUALIFIER = re.compile(r"^\s*(?:in air and close|in air|close|air)\s*,?\s*", re.IGNORECASE)
_INPUT_HEAD = re.compile(
    r"^\s*(?:\(|hold\b|qcf|qcb|hcf|hcb|(?:ub|uf|db|df|[bfdun])\b|[ABCDPK]{1,4}(?![A-Za-z]))",
    re.IGNORECASE,
)
"""A command the trainer could recognise opens with a direction, a shorthand
motion or a button. Anything else names the move it follows on from."""

_HELD_BUTTON = re.compile(r"\+\s*hold\b", re.IGNORECASE)
"""``+ hold P``: the button is held rather than tapped. Every press is momentary
to the engine, so Yuri's ``d, df, f + hold P`` Haoh Shou Ko Ken would be
indistinguishable from the ``d, df, f + P`` Ko Ou Ken listed right above it."""


def to_shorthand(command: str) -> str:
    """Rewrite one command into the dialect ``normalise`` reads."""
    text = command
    if _TRAILING_AIR.search(text):
        text = f"In air, {_TRAILING_AIR.sub('', text)}"
    text = _CHARGED.sub(lambda match: f"Charge {match.group(1)},{match.group(2)}", text)
    text = _REPEATED.sub(lambda match: f"{match.group(1)},{match.group(1)}", text)
    return _MASHED.sub(_buttons, _BUTTONS.sub(_buttons, text))


def _buttons(match: re.Match[str]) -> str:
    """One button clause, as the alternation ``normalise`` reads."""
    options = [option for option in _SPLIT_CHOICE.split(match.group(1)) if option]
    return "+ " + " / ".join(" + ".join(TO_SHORTHAND[letter] for letter in option) for option in options)


_EITHER = re.compile(r"^\s*(?:either|after)\s+", re.IGNORECASE)
"""How the guides sometimes open a chain link: "either Shining Crystal Bit, ..."."""


def split_parent(command: str, so_far: Sequence[MoveName]) -> tuple[str, str]:
    """A chain link's parent and its own command, or ``("", "")``.

    These guides write a link as the move it continues, a comma, then the input
    for this half: ``114 Shiki Aragami, d, df, f + P``. The head is only taken
    as a parent when it names a move the character already has - otherwise it
    is prose this cannot model, and the move stays struck through as before
    rather than gaining a link to nothing.

    A move name inside the head is preferred, longest first, so ``Strong Hien
    Zan`` finds ``Hien Zan``, and Naoe Shigen's ``Kai`` finds ``Kai`` rather
    than the ``Akkai`` that also contains it. Only when nothing matches that way
    is the head read as an abbreviation of a name - Setsuna's ``Go`` for ``Mumei
    - Go``, and the heads that drop the ``(DM)`` the roster keeps. The shortest
    candidate wins there, being the one the head accounts for most of.
    """
    head, comma, tail = command.partition(",")
    if not comma or not tail.strip():
        return "", ""
    head = _EITHER.sub("", head).strip()
    # An ordinary command is direction, comma, direction, and its head is an
    # input rather than a name. Without this the abbreviation pass below would
    # read the ``d`` of every ``d, df, f`` as any move with a d in its name.
    if not head or _INPUT_HEAD.match(head):
        return "", ""
    named = [move.name for move in so_far if move.name and move.name in head]
    if named:
        return max(named, key=len), tail.strip()
    abbreviated = [move.name for move in so_far if move.name and head in move.name]
    if abbreviated:
        return min(abbreviated, key=len), tail.strip()
    return "", ""


def unmodelled(command: str) -> str:
    """Why the trainer cannot recognise this command, or ``""`` if it may try.

    Both cases would otherwise parse into something plausible and wrong. Kyo's
    ``114 Shiki Aragami, d, df, f + P`` still has a quarter circle in it and
    would come out a plain fireball; Yuri's ``d, df, f + hold P`` *is* a plain
    fireball once the hold is dropped, and a duplicate of the move above it.
    """
    if not _INPUT_HEAD.match(_QUALIFIER.sub("", command)):
        return "follows on from another move"
    if _HELD_BUTTON.search(command):
        return "the button is held, which the trainer cannot tell from a tap"
    return ""
