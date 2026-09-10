"""Fetch the reference guides the parsers read.

Run ``python -m motioninput_tui_guides`` from the repository root to fetch
anything missing, or with ``--list`` to see the catalogue and what is present.

This lives outside the ``motioninput_tui`` package on purpose, so it is not
shipped in the wheel. It is a development tool for regenerating roster data.
"""

import argparse
import sys
from pathlib import Path

from motioninput_tui.utils.logger import get_logger, setup_logger_cli

from .catalog import DEFAULT_DEST, CatalogError, Guide, get_guide, load_guides, sha256_file
from .fetch import DEFAULT_DELAY_S, DEFAULT_TIMEOUT_S, MissingDependencyError, Status, fetch_all

logger = get_logger(__name__)


def _get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python -m motioninput_tui_guides", description=__doc__)
    parser.add_argument("--game", action="append", help="Fetch only this guide. Repeatable.")
    parser.add_argument("--dest", type=Path, default=DEFAULT_DEST, help=f"Where to write (default: {DEFAULT_DEST}).")
    parser.add_argument("--force", action="store_true", help="Re-fetch guides that are already present.")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY_S, help="Seconds between requests.")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_S, help="Per-request timeout in seconds.")
    parser.add_argument("--list", action="store_true", help="List the catalogue and exit.")
    parser.add_argument(
        "--checksums",
        action="store_true",
        help="Print the SHA-256 of each guide on disk, to paste into sources.json, and exit.",
    )
    parser.add_argument("-v", action="count", default=0, help="Increase verbosity.")
    return parser.parse_args()


def _checksum_state(guide: Guide, dest: Path) -> str:
    """A short word for how the on-disk guide compares to its recorded sha256."""
    ok = guide.checksum_ok(dest)
    if ok is True:
        return ", sha256 ok"
    if ok is False:
        return ", SHA-256 MISMATCH"
    return ""


def _print_catalogue(dest: Path) -> int:
    for guide in load_guides():
        path = guide.path(dest)
        state = f"{path.stat().st_size:,} bytes{_checksum_state(guide, dest)}" if path.exists() else "missing"
        logger.info("%-8s %-46s %s", guide.key, guide.name, state)
        logger.info("         %s", guide.credit or guide.url)
    return 0


def _print_checksums(dest: Path) -> int:
    for guide in load_guides():
        path = guide.path(dest)
        logger.info("%-8s %s", guide.key, sha256_file(path) if path.is_file() else "missing")
    return 0


def main() -> int:
    """Fetch the guides named on the command line, or any that are missing."""
    args = _get_args()
    setup_logger_cli(args.v)

    try:
        guides = [get_guide(key) for key in args.game] if args.game else list(load_guides())
    except (CatalogError, KeyError) as exc:
        logger.error("%s", exc)  # ruff: ignore[error-instead-of-exception] - a traceback helps nobody here
        return 2

    if args.list:
        return _print_catalogue(args.dest)

    if args.checksums:
        return _print_checksums(args.dest)

    logger.info("These guides are copyright their authors. Personal use only, do not redistribute.")
    try:
        results = fetch_all(guides, args.dest, force=args.force, delay=args.delay, timeout=args.timeout)
    except MissingDependencyError as exc:
        logger.error("%s", exc)  # ruff: ignore[error-instead-of-exception] - the message is the whole point
        return 2

    for result in results:
        log = logger.info if result.ok else logger.warning
        log("%-8s %-8s %s", result.guide.key, result.status.value, result.detail)

    failed = [result for result in results if not result.ok]
    fetched = sum(1 for result in results if result.status is Status.FETCHED)
    logger.info("%d fetched, %d already present, %d failed", fetched, len(results) - fetched - len(failed), len(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
