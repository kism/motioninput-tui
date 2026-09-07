"""The list of reference guides and where each one came from."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cache
from pathlib import Path

SOURCES_PATH = Path(__file__).parent / "sources.json"
DEFAULT_DEST = Path("references")


@dataclass(frozen=True, slots=True)
class Guide:
    """One reference guide: its game, its source page and where it lands."""

    key: str
    name: str
    url: str
    credit: str = ""
    filename: str = ""

    def path(self, dest_dir: Path = DEFAULT_DEST) -> Path:
        """Where this guide is stored locally."""
        return dest_dir / (self.filename or f"{self.key}.txt")


class CatalogError(ValueError):
    """Raised when sources.json is missing fields or malformed."""


@cache
def load_guides(path: Path = SOURCES_PATH) -> tuple[Guide, ...]:
    """Read the guide catalogue. Cached, since it does not change at runtime."""
    with path.open(encoding="utf-8") as handle:
        raw = json.load(handle)

    guides = []
    for index, entry in enumerate(raw.get("guides", [])):
        missing = [field for field in ("key", "name", "url") if not entry.get(field)]
        if missing:
            message = f"Guide {index} in {path} is missing: {', '.join(missing)}"
            raise CatalogError(message)
        guides.append(
            Guide(
                key=str(entry["key"]),
                name=str(entry["name"]),
                url=str(entry["url"]),
                credit=str(entry.get("credit", "")),
                filename=str(entry.get("filename", "")),
            )
        )

    keys = [guide.key for guide in guides]
    duplicates = {key for key in keys if keys.count(key) > 1}
    if duplicates:
        message = f"Duplicate guide keys in {path}: {', '.join(sorted(duplicates))}"
        raise CatalogError(message)
    return tuple(guides)


def get_guide(key: str, path: Path = SOURCES_PATH) -> Guide:
    """Look up one guide by its short name."""
    for guide in load_guides(path):
        if guide.key == key:
            return guide
    known = ", ".join(guide.key for guide in load_guides(path))
    message = f"Unknown guide {key!r}. Known guides: {known}"
    raise KeyError(message)
