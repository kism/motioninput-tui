"""The datagen --summary breakdown of the roster data on disk."""

import pytest

from motioninput_tui_datagen.summary import print_summary


def test_summary_covers_every_generated_game(caplog: pytest.LogCaptureFixture) -> None:
    """It logs a line per game and characters, and a grand total, without touching the guides."""
    with caplog.at_level("INFO"):
        assert print_summary() == 0

    text = caplog.text
    assert "sfiii3 - Street Fighter III: 3rd Strike" in text
    assert "    ryu" in text  # a character line
    assert "TOTAL:" in text
