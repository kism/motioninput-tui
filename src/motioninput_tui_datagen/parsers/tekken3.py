"""Parser for the Tekken 3 FAQ.

A character is a starred heading, then rows of ``command - Name``, with two
sub-sections marked off by plus signs that are not moves: ``+Juggles+`` (combo
recipes, whose difficulty letters would otherwise read as buttons) and
``+Profile+`` (height, blood type).

The dialect is unlike every other guide here, because the game is::

    lp,rp,lk            - One Two -> Kick
    df+lp,rp            - Elbow Pistons (NJ)
    f,F+rp              - Straight Fist
    d,df,f+lp           - Uppercut (NJ)
     ^b+rp              - Double Punishment (Gutpunch must connect)

Most of it is *strings*: presses in order, which :mod:`normalise` reads as a
:attr:`~motioninput_tui.engine.motions.MotionKind.SEQUENCE`. A comma separates
one press from the next and a plus joins the ones made together, so the comma
means something different here than in a guide writing ``d, df, f``. Both
appear - the game has a handful of quarter circles - and telling them apart is
already `normalise`'s job: a run with a button in front of a comma is a string,
anything else is a motion.

Four things need translating before that:

``lp rp lk rk`` are the four limbs, and are mapped onto Street Fighter buttons
for parsing and back onto the Tekken panel afterwards, exactly as the Neo Geo
guides are.

**Case is meaning.** A lower-case direction is a tap and an upper-case one is
held, so ``f,F`` is the dash: tap forward, then hold it. The trainer has no
notion of holding a direction *through* a press, so both become the tap, which
is what makes that dash the ``f,f`` double tap the engine does model.

``~`` means "immediately following", which is a string written tighter rather
than a different thing, so it becomes the comma it stands for.

``^`` at the front marks a row as continuing the move above it, and how far the
row is indented says *which* move: the guide nests a string four deep in
places, so a row's parent is the nearest one above it that starts further left.
That is a whole quarter of this roster.
"""

import re
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from motioninput_tui.engine.notation import Button, ButtonRequirement
from motioninput_tui.games.models import Move
from motioninput_tui_datagen.common import ParseReport, build_move, finish_character

if TYPE_CHECKING:
    from motioninput_tui.engine.motions import MotionSpec
    from motioninput_tui.games.models import Character

SECTION_START = "*Bryan Fury*"
SECTION_END = "*Throw & Reversal Counters*"

_HEADING = re.compile(r"^\*([A-Za-z][A-Za-z.'/ ]+?)\*(?:\s*-.*)?$")
"""``*Jin Kazama*``, sometimes with a note after it saying the character is in
the console version only."""

_SUBHEADING = re.compile(r"^\+(.+)\+\s*$")
_NOT_MOVES = ("Juggles", "Profile")
"""The two sub-sections that are not a move list and run to the end of the
character. ``+Juggles+`` is combo recipes, whose ``B``/``I``/``E`` difficulty
column reads as buttons if it is let through.

The other sub-sections a character can carry - how to unlock them, and the
legend two of them have of their own - come *before* the moves, so switching
off at one would switch off the whole character. Their rows are dropped by
:func:`_row` instead, on having no input outside their brackets."""

_SEPARATOR = " - "

_LIMBS = {"lp": "LP", "rp": "HP", "lk": "LK", "rk": "HK"}
"""The four limbs in the dialect ``normalise`` reads. Which SF button stands in
for which is arbitrary and only has to be one-to-one, so :func:`_to_panel` can
put it back."""

_TO_TEKKEN = {Button.LP: Button.SQUARE, Button.HP: Button.TRIANGLE, Button.LK: Button.CROSS, Button.HK: Button.CIRCLE}
_PANEL_ORDER = (Button.SQUARE, Button.TRIANGLE, Button.CROSS, Button.CIRCLE)

_LIMB_TOKEN = re.compile(r"\b(lp|rp|lk|rk)\b")
_HELD_DIRECTION = re.compile(r"\b([FBUD])\b")
"""An upper-case direction is held rather than tapped, which the trainer cannot
tell from a tap: every press is momentary to it."""

_ASIDE = re.compile(r"\([^)]*\)")

_STANCE = re.compile(r"\b(ss|WS|WC|FC)\b")
"""A state rather than an input: a sidestep, or getting up from a crouch. The
trainer reads what you press and has no notion of either, and left alone they
are simply dropped as noise - which would take Eddy's ``ss,lk+rk,lk+rk,lk+rk``
and his ``ss,lk+rk`` and call them the same move."""

_STANCE_REASON = "needs a sidestep or a crouch, which the trainer has no model of"

_INPUT_TOKEN = re.compile(r"(?<![A-Za-z])(lp|rp|lk|rk|ub|uf|db|df|[fbudn])(?![A-Za-z])", re.IGNORECASE)
"""Something a player could press. Mokujin's section is a table of the stances
he copies, written ``Bryan Fury - Walks up to you...``, which has a move row's
shape and no input in it whatever; without this he arrives with 33 of them."""
_CHAIN = "^"
_IMMEDIATELY = "~"


def parse(text: str) -> tuple[list[Character], ParseReport]:
    """Extract every character and their moves from the Tekken 3 FAQ."""
    report = ParseReport()
    characters: list[Character] = []

    name = ""
    moves: list[Move] = []
    chain: list[tuple[int, str]] = []
    collecting = False

    def flush() -> None:
        character = finish_character(name, "", moves, report)
        if character is not None:
            characters.append(character)

    for line in _section(text):
        heading = _HEADING.match(line.strip())
        if heading is not None:
            flush()
            name, moves, chain, collecting = _character_name(heading.group(1)), [], [], True
            continue

        sub = _SUBHEADING.match(line.strip())
        if sub is not None:
            collecting = not any(word in _NOT_MOVES for word in sub.group(1).split())
            continue

        if not collecting or _SEPARATOR not in line:
            continue
        row = _row(line)
        if row is not None:
            moves.append(_tekken_move(row, report, name, _parent(chain, row)))

    flush()
    return characters, report


def _section(text: str) -> list[str]:
    lines = text.splitlines()
    start = next(index for index, line in enumerate(lines) if line.startswith(SECTION_START))
    end = next(index for index in range(start + 1, len(lines)) if lines[index].startswith(SECTION_END))
    return lines[start:end]


def _character_name(heading: str) -> str:
    """The name a heading gives, taking the first of a shared move list.

    Two pairs share one - Eddy with Tiger, Nina with Anna - and the guide lists
    them as one character rather than repeating the moves.
    """
    return heading.split("/", maxsplit=1)[0].strip()


@dataclass(frozen=True, slots=True)
class _Row:
    """One ``command - Name`` line, before its command is read."""

    indent: int
    command: str
    name: str
    chained: bool
    """Whether the row opened with ``^``, marking it as continuing the one above."""


def _row(line: str) -> _Row | None:
    """One ``command - Name`` line pulled apart."""
    command, _, move_name = line.partition(_SEPARATOR)
    indent = len(command) - len(command.lstrip())
    command = command.strip()
    chained = command.startswith(_CHAIN)
    command, move_name = command.removeprefix(_CHAIN).strip(), move_name.strip()
    # A legend row is a bracketed marker and its meaning, "(FB) - ...", and a
    # prose row names a character; both have a move row's shape and no input.
    if not command or not move_name or not _INPUT_TOKEN.search(_ASIDE.sub("", command)):
        return None
    return _Row(indent=indent, command=command, name=move_name, chained=chained)


def _parent(chain: list[tuple[int, str]], row: _Row) -> str:
    """The move this row continues, and keep the stack of open ones current.

    The caret says a row is a follow-up and the indent says of what: the
    nearest line above it that starts further left. A row without a caret
    closes whatever was open, so a plain move never inherits the string before
    it.
    """
    while chain and chain[-1][0] >= row.indent:
        chain.pop()
    parent = chain[-1][1] if chain and row.chained else ""
    chain.append((row.indent, row.name))
    # Lei's Low Cartwheel is listed twice, the second time under itself, which
    # is the guide saying it can be done again. The standalone row already says
    # that input gives that move, so the link would only be a duplicate of it.
    return "" if parent == row.name else parent


def _tekken_move(row: _Row, report: ParseReport, character: str, parent: str) -> Move:
    """One row, parsed in Street Fighter notation and put back on this panel."""
    command, name = row.command, row.name
    if _STANCE.search(command):
        # Kept in the move list, struck through, rather than reduced to the
        # presses inside it: the stance is half of what the move is.
        report.note(character, name, _STANCE_REASON)
        return Move(name=name, command=command, follows=parent)
    move = build_move(name, _to_shorthand(command), report, character, follows=parent)
    if move.motion is None:
        return replace(move, command=command)
    return replace(move, command=command, motion=_to_panel(move.motion, command))


def _to_shorthand(command: str) -> str:
    """Rewrite one command into the dialect ``normalise`` reads."""
    text = _ASIDE.sub(" ", command).replace(_IMMEDIATELY, ",")
    text = _HELD_DIRECTION.sub(lambda match: match.group(1).lower(), text)
    return _LIMB_TOKEN.sub(lambda match: _LIMBS[match.group(1)], text).strip().strip(",")


def _to_panel(motion: MotionSpec, command: str) -> MotionSpec:
    """Put a motion's buttons back onto the Tekken panel, steps included."""
    sequence = tuple(replace(step, buttons=_panel_buttons(step.buttons)) for step in motion.sequence)
    return replace(motion, buttons=_panel_buttons(motion.buttons), sequence=sequence, notation=command.strip())


def _panel_buttons(requirement: ButtonRequirement) -> ButtonRequirement:
    """The same requirement expressed in this game's four limbs."""
    mapped = frozenset(_TO_TEKKEN.get(button, button) for button in requirement.allowed)
    names = [button.value for button in _PANEL_ORDER if button in mapped]
    joined = "+" if requirement.count >= len(names) else "/"
    return ButtonRequirement(mapped, requirement.count, joined.join(names))
