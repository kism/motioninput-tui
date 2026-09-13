"""One parser per game. Each module exposes ``parse(text) -> (characters, report)``.

``__main__`` builds the game-key -> parser mapping from these.
"""

from . import hsf2, kof98, kof2001, lastbld2, samsh5sp, samsho2, sfa3, sfiii3, usfiv

__all__ = ["hsf2", "kof98", "kof2001", "lastbld2", "samsh5sp", "samsho2", "sfa3", "sfiii3", "usfiv"]
