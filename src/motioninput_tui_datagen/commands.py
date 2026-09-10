"""Corrected commands, where a reference guide has a move's input wrong.

Distinct from :mod:`names`, which fixes what a character is *called*. This one
fixes what the guide says you have to *press*, which is worse: a wrong name is
merely wrong, but a wrong command makes the trainer teach an input the game does
not accept, and the player has no way to tell that from their own execution.

Only for outright errors, checked against the real game. A command the parser
merely fails to model is not one of these - it belongs in ``normalise``'s tables,
or stays untrainable and struck through in the move list.

An override is keyed by the character key and the move name as the roster ends
up holding them, which is after :func:`names.apply_overrides` has run, so it is
written the way the trainer shows it. The replacement is parsed by the ordinary
:func:`normalise.parse_command`, so it is written in the same dialect a guide
would use and gains nothing the parser cannot already read.
"""

from dataclasses import replace
from typing import TYPE_CHECKING

from motioninput_tui.controls.buttons import NEO_GEO
from motioninput_tui.utils.logger import get_logger

from .common import categorise
from .neogeo import neo_buttons
from .normalise import parse_command

if TYPE_CHECKING:
    from motioninput_tui.controls.buttons import ButtonSet
    from motioninput_tui.games.models import Character, Move

logger = get_logger(__name__)

OVERRIDES: dict[str, dict[tuple[str, str], str]] = {
    "sfa3": {
        # The guide gives `qcf,d,df + K`, which is a quarter circle into a
        # dragon punch and is not the move. Alpha 3 wants two quarter circles,
        # like her other two supers. As written the guide's version does come
        # out in the trainer, so this was not a parser gap - it was the trainer
        # faithfully teaching the guide's mistake.
        ("sakura", "Midare-zakura"): "qcf,qcf + K",
    },
}
"""Game key -> {(character key, move name): the command that actually works}."""


def apply_command_overrides(game_key: str, characters: list[Character], buttons: ButtonSet) -> list[Character]:
    """Re-read the commands this game has a correction for."""
    table = OVERRIDES.get(game_key)
    if not table:
        return characters

    unused = set(table)

    def corrected(character_key: str, move: Move) -> Move:
        command = table.get((character_key, move.name))
        if command is None:
            return move
        unused.discard((character_key, move.name))

        parsed = parse_command(command)
        if parsed.motion is None:
            # The correction itself does not parse, which is a mistake in this
            # file rather than in the guide. Leave the guide's move alone.
            logger.warning("Correction %r for %s does not parse: %s", command, move.name, parsed.reason)
            return move

        motion = parsed.motion
        if buttons is NEO_GEO:
            # The engine matches buttons by identity, so a Neo Geo roster needs
            # the requirement put back onto A B C D as its own parser would.
            motion = replace(motion, buttons=neo_buttons(motion.buttons))
        logger.debug("Correcting %s / %s in %s to %r", character_key, move.name, game_key, command)
        return replace(
            move,
            command=command,
            motion=motion,
            category=categorise(move.name, motion.kind, motion.buttons.count),
        )

    result = [
        replace(character, moves=tuple(corrected(character.key, move) for move in character.moves))
        for character in characters
    ]
    for entry in sorted(unused):
        # Silently doing nothing would hide a typo, or a guide that has been
        # fixed since - in which case the override should simply go.
        logger.warning("No move %r in %s to correct", entry, game_key)
    return result
