"""Preferred character names, where a reference guide uses another one.

The guides were written by different authors years apart, so they disagree
about what a character is called. The Alpha 3 and 3rd Strike guides both list
Ken as "Ken Masters", which is not how anybody refers to him.

An override is keyed by the character key the guide produced, since that is
stable across the title casing and spacing the guides vary in. The replacement
name is what the trainer displays, and the key is rebuilt from it, so renaming
"Ken Masters" to "Ken" turns ``ken-masters`` into ``ken`` as well. That means an
override changes ``--character`` and the saved config, so it is worth doing at
the point the roster is generated rather than papering over it later.
"""

from dataclasses import replace
from typing import TYPE_CHECKING

from motioninput_tui.utils.logger import get_logger

from .common import character_key

if TYPE_CHECKING:
    from motioninput_tui.games.models import Character

logger = get_logger(__name__)

OVERRIDES: dict[str, dict[str, str]] = {
    "sfa3": {
        "dan-hibiki": "Dan",
        "edmond-honda": "E. Honda",
        "karin-kanzuki": "Karin",
        "ken-masters": "Ken",
        "rainbow-mika": "R. Mika",
        "rolento-schugerg": "Rolento",
        "sakura-kasugano": "Sakura",
    },
    "sfiii3": {
        # The 3rd Strike guide uses the Japanese name; the Super Turbo one does
        # not, and a roster that calls the same character two things is worse
        # than either choice on its own.
        "gouki": "Akuma",
        "ken-masters": "Ken",
    },
}
"""Game key -> {key the guide produced: name to use instead}."""


def apply_overrides(game_key: str, characters: list[Character]) -> list[Character]:
    """Rename the characters this game has an override for."""
    table = OVERRIDES.get(game_key)
    if not table:
        return characters

    unused = set(table)
    renamed = []
    for character in characters:
        preferred = table.get(character.key)
        if preferred is None:
            renamed.append(character)
            continue
        unused.discard(character.key)
        logger.debug("Renaming %s to %s in %s", character.key, preferred, game_key)
        renamed.append(replace(character, key=character_key(preferred), name=preferred))

    for key in sorted(unused):
        # Silently doing nothing would hide a typo, or a guide that has changed.
        logger.warning("No character %r in %s to rename to %r", key, game_key, table[key])
    _warn_on_collisions(game_key, renamed)
    return renamed


def _warn_on_collisions(game_key: str, characters: list[Character]) -> None:
    """A rename landing on another character's key would hide one of them."""
    seen: set[str] = set()
    for character in characters:
        if character.key in seen:
            logger.warning("Two characters share the key %r in %s after renaming", character.key, game_key)
        seen.add(character.key)
