"""The list of reference guides and where each one came from."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from functools import cache
from pathlib import Path

SOURCES_PATH = Path(__file__).parent / "sources.json"
DEFAULT_DEST = Path("references")


def _canonical_text(text: str) -> str:
    """The form a guide is checksummed in, so trivial whitespace never breaks it.

    Leading blank lines are dropped, every whitespace-only line is emptied, and
    the file ends in exactly one newline. A guide re-fetched or hand-edited with
    only surrounding whitespace changed still matches its recorded ``sha256``.
    """
    lines = [line if line.strip() else "" for line in text.split("\n")]
    while lines and not lines[0]:
        lines.pop(0)
    return "\n".join(lines).rstrip("\n") + "\n"


def canonicalise_file(path: Path) -> bool:
    """Rewrite ``path`` in canonical form. Returns whether it changed on disk."""
    original = path.read_text(encoding="utf-8")
    canonical = _canonical_text(original)
    if canonical == original:
        return False
    path.write_text(canonical, encoding="utf-8")
    return True


def sha256_file(path: Path) -> str:
    """Hex SHA-256 of a guide's canonical text, the form stored in sources.json."""
    return hashlib.sha256(_canonical_text(path.read_text(encoding="utf-8")).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class Guide:
    """One reference guide: its game, its source page and where it lands."""

    key: str
    name: str
    url: str
    credit: str = ""
    filename: str = ""
    sha256: str = ""

    def path(self, dest_dir: Path = DEFAULT_DEST) -> Path:
        """Where this guide is stored locally."""
        return dest_dir / (self.filename or f"{self.key}.txt")

    def checksum_ok(self, dest_dir: Path = DEFAULT_DEST) -> bool | None:
        """Whether the local copy matches the recorded ``sha256``.

        ``None`` when there is nothing to check: no checksum is recorded, or the
        guide is not on disk yet.
        """
        path = self.path(dest_dir)
        if not self.sha256 or not path.is_file():
            return None
        return sha256_file(path) == self.sha256


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
                sha256=str(entry.get("sha256", "")).lower(),
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
