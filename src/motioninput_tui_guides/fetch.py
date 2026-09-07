"""Fetch reference guides from GameFAQs into a local, gitignored directory.

The guides are copyrighted by their authors and explicitly may not be
redistributed, which is why they are not committed and each user fetches their
own copy of pages they could equally read in a browser. Anything already
present is left alone, so a full run normally makes no requests at all.

This module sits outside the ``motioninput_tui`` package so it is not shipped
in the wheel, and its dependencies live in a separate extra. Install them with
``uv sync --extra guides``.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from motioninput_tui.utils.logger import get_logger

from .catalog import DEFAULT_DEST

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from .catalog import Guide

logger = get_logger(__name__)

HTTP_OK = 200

MIN_BYTES = 1024
"""Anything smaller than this is an error page, not a guide."""

DEFAULT_DELAY_S = 3.0
"""Pause between requests. These are large static documents fetched once."""

DEFAULT_TIMEOUT_S = 30

_CHECKSUM_MISMATCH = "its SHA-256 does not match the sha256 recorded in sources.json"

_BLOCK_MARKERS = (
    "just a moment",
    "checking your browser",
    "cf-browser-verification",
    "enable javascript and cookies to continue",
    "attention required",
)


class Status(StrEnum):
    """What happened to one guide."""

    FETCHED = "fetched"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class Result:
    """The outcome of fetching one guide."""

    guide: Guide
    status: Status
    path: Path
    detail: str = ""

    @property
    def ok(self) -> bool:
        """Whether the guide is now on disk."""
        return self.status is not Status.FAILED


class MissingDependencyError(ImportError):
    """Raised when the optional fetching dependencies are not installed."""

    def __init__(self, package: str) -> None:
        """Point the user at the extra that provides it."""
        super().__init__(f"{package} is needed to fetch guides. Install it with: uv sync --extra guides")


class FetchError(RuntimeError):
    """Raised when a guide could not be retrieved or looked wrong."""


def _http_get(url: str, timeout: float) -> str:
    """Fetch a page as text.

    Prefers curl_cffi, which presents a browser-like TLS handshake. GameFAQs
    sits behind Cloudflare and a plain client is usually turned away.
    """
    try:
        from curl_cffi import requests as curl_requests  # ruff: ignore[import-outside-top-level] - optional extra
    except ImportError:
        curl_requests = None

    if curl_requests is not None:
        response = curl_requests.get(url, impersonate="chrome", timeout=timeout)
        status, text = response.status_code, response.text
    else:
        try:
            # Not in the guides extra: a plain client rarely gets past Cloudflare,
            # but it is a usable fallback where curl_cffi has no wheel.
            import requests  # ruff: ignore[import-outside-top-level]  # ty: ignore[unresolved-import]
        except ImportError as exc:
            package = "curl_cffi (or requests)"
            raise MissingDependencyError(package) from exc
        response = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        status, text = response.status_code, response.text

    if status != HTTP_OK:
        message = f"HTTP {status}"
        raise FetchError(message)
    return text


def _looks_blocked(html: str) -> bool:
    head = html[:4000].lower()
    return any(marker in head for marker in _BLOCK_MARKERS)


def extract_guide_text(html: str) -> str:
    """Pull the plain text guide out of a GameFAQs page.

    These are plain text FAQs wrapped in HTML, so the body is a single
    preformatted block. Several selectors are tried because the markup has
    changed over the years.
    """
    try:
        from bs4 import BeautifulSoup  # ruff: ignore[import-outside-top-level] - optional extra
    except ImportError as exc:
        package = "beautifulsoup4"
        raise MissingDependencyError(package) from exc

    soup = BeautifulSoup(html, "html.parser")
    for selector in ("div.faqtext pre", "div.faqtext", "#faqwrap pre", "pre"):
        blocks = soup.select(selector)
        if blocks:
            # A guide split over several blocks still reads in order.
            longest = max(blocks, key=lambda block: len(block.get_text()))
            return longest.get_text()
    return ""


def _checked(guide: Guide, dest_dir: Path, ok_status: Status, detail: str, hint: str) -> Result:
    """Turn ``detail`` into a Result, failing it if the guide's SHA-256 is wrong.

    ``hint`` is appended to the failure message to say how to recover.
    """
    if guide.checksum_ok(dest_dir) is False:
        return Result(guide, Status.FAILED, guide.path(dest_dir), f"{detail}, but {_CHECKSUM_MISMATCH}; {hint}")
    return Result(guide, ok_status, guide.path(dest_dir), detail)


def fetch_guide(
    guide: Guide,
    dest_dir: Path = DEFAULT_DEST,
    *,
    force: bool = False,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> Result:
    """Fetch one guide, unless it is already on disk.

    A guide that comes back under :data:`MIN_BYTES` is treated as a failure and
    nothing is written, so a block page never masquerades as a reference file.

    When the catalogue records a ``sha256`` for the guide, the copy on disk (or
    the one just fetched) is checked against it, so a changed upstream page or a
    corrupt file is caught before the parsers run.
    """
    path = guide.path(dest_dir)
    if path.exists() and not force:
        detail = f"already present ({path.stat().st_size:,} bytes)"
        return _checked(guide, dest_dir, Status.SKIPPED, detail, "re-fetch with --force")

    try:
        html = _http_get(guide.url, timeout)
    except MissingDependencyError:
        raise
    except Exception as exc:  # ruff: ignore[blind-except] - one bad guide must not stop the rest
        return Result(guide, Status.FAILED, path, str(exc))

    if _looks_blocked(html):
        return Result(guide, Status.FAILED, path, "blocked by anti-bot check; try again later")

    text = extract_guide_text(html).strip()
    if len(text.encode("utf-8")) < MIN_BYTES:
        return Result(guide, Status.FAILED, path, f"only {len(text)} characters extracted, looks like an error page")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text + "\n", encoding="utf-8")
    size = f"{path.stat().st_size:,} bytes"
    return _checked(guide, dest_dir, Status.FETCHED, size, "the guide may have changed upstream")


def fetch_all(
    guides: Sequence[Guide],
    dest_dir: Path = DEFAULT_DEST,
    *,
    force: bool = False,
    delay: float = DEFAULT_DELAY_S,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> list[Result]:
    """Fetch several guides, pausing between actual requests."""
    results = []
    requested = False
    for guide in guides:
        if requested and delay > 0:
            time.sleep(delay)
        result = fetch_guide(guide, dest_dir, force=force, timeout=timeout)
        requested = result.status is not Status.SKIPPED
        results.append(result)
    return results
