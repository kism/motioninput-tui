"""Fixtures shared across the whole suite.

The motion tests have their own harness and fixtures in
``tests/engine/test_motions/``, since they all need the same kind of setup.
"""

from __future__ import annotations

import pytest

from motioninput_tui.controls import gamepad


@pytest.fixture(autouse=True)  # ruff: ignore[pytest-fixture-autouse] - a plugged-in pad must never leak into any test
def _no_real_gamepad(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the suite off real hardware.

    pygame still loads (so the gamepad layout stays available), but no physical
    pad is ever opened. Tests that need one re-patch ``_first_controller``.
    """
    monkeypatch.setattr(gamepad, "_first_controller", lambda _pygame: None)
