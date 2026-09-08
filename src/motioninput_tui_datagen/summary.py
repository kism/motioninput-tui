"""Print a per-character breakdown of the generated rosters.

Reads the committed ``games/data/*.json`` through the normal loader, so it
reflects what is on disk now, not a fresh parse. Run it after a datagen run to
eyeball what changed:

    python -m motioninput_tui_datagen --summary
"""

from collections import Counter

from motioninput_tui.games.loader import available_games
from motioninput_tui.utils.logger import get_logger

logger = get_logger(__name__)


def _pct(part: int, whole: int) -> int:
    return round(100 * part / whole) if whole else 0


def print_summary() -> int:
    """Log every generated game, its characters and their move counts."""
    games = [game for game in available_games() if game.source]

    grand_chars = grand_moves = grand_trainable = 0
    for game in games:
        characters = game.characters
        moves = sum(len(character.moves) for character in characters)
        trainable = sum(len(character.trainable_moves) for character in characters)
        categories = Counter(move.category for character in characters for move in character.moves)

        grand_chars += len(characters)
        grand_moves += moves
        grand_trainable += trainable

        logger.info("%s - %s", game.key, game.name)
        logger.info(
            "  %d characters, %d moves, %d trainable (%d%%), %d not",
            len(characters),
            moves,
            trainable,
            _pct(trainable, moves),
            moves - trainable,
        )
        logger.info("  by category: %s", ", ".join(f"{name} {count}" for name, count in categories.most_common()))
        for character in characters:
            count = len(character.moves)
            trained = len(character.trainable_moves)
            logger.info("    %-24s %3d/%-3d trainable", character.key, trained, count)

    logger.info(
        "TOTAL: %d games, %d characters, %d moves, %d trainable (%d%%)",
        len(games),
        grand_chars,
        grand_moves,
        grand_trainable,
        _pct(grand_trainable, grand_moves),
    )
    return 0
