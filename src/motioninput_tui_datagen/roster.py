"""Write a generated roster to the packaged data directory."""

import json
from typing import TYPE_CHECKING

from motioninput_tui.games.loader import DATA_DIR
from motioninput_tui.games.rulesets import get_spec

if TYPE_CHECKING:
    from pathlib import Path

    from motioninput_tui.games.models import Character


def write_game(key: str, characters: list[Character]) -> Path:
    """Write a generated roster to the package data directory."""
    spec = get_spec(key)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / f"{spec.key}.json"
    payload = {
        "key": spec.key,
        "name": spec.name,
        "source": spec.reference,
        "characters": [character.to_dict() for character in characters],
    }
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=1, ensure_ascii=False)
        handle.write("\n")
    return path
