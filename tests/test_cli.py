"""Startup decisions made before the interface takes over the terminal."""

import json
import sys
from typing import TYPE_CHECKING

import pytest

from motioninput_tui.__main__ import main

if TYPE_CHECKING:
    from pathlib import Path

    from motioninput_tui.config import Config


@pytest.fixture
def saved(tmp_path: Path):
    """Write a config file and hand back its path."""

    def write(**values: object) -> Path:
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"layout": "keyboard-left", **values}), encoding="utf-8")
        return path

    return write


@pytest.fixture
def launched(monkeypatch: pytest.MonkeyPatch) -> list[Config]:
    """Capture the config the app would have been started with."""
    started: list[Config] = []

    class FakeApp:
        def __init__(self, config: Config, **_kwargs: object) -> None:
            started.append(config)

        def run(self) -> None:
            pass

    monkeypatch.setattr("motioninput_tui.tui.MotionInputApp", FakeApp)
    return started


def test_a_remembered_character_is_kept(saved, launched, monkeypatch) -> None:
    path = saved(game="sfiii3", character="ken")
    monkeypatch.setattr(sys, "argv", ["motioninput-tui", "--config", str(path)])

    assert main() == 0
    assert launched[0].character == "ken"


def test_a_remembered_character_who_has_gone_is_forgotten(saved, launched, monkeypatch) -> None:
    """Renaming a character in the rosters must not stop the app starting."""
    path = saved(game="sfiii3", character="ken-masters")
    monkeypatch.setattr(sys, "argv", ["motioninput-tui", "--config", str(path)])

    assert main() == 0
    assert launched[0].character is None
    assert launched[0].game == "sfiii3"


def test_an_unknown_character_asked_for_on_the_command_line_is_an_error(saved, launched, monkeypatch) -> None:
    path = saved()
    monkeypatch.setattr(
        sys, "argv", ["motioninput-tui", "--config", str(path), "--game", "sfiii3", "--character", "ken-masters"]
    )

    assert main() == 1
    assert launched == []


def test_a_game_on_the_command_line_reopens_its_own_character(saved, launched, monkeypatch) -> None:
    """--game alone picks up that game's remembered character, not the last game's."""
    path = saved(game="hsf2", character="ryu", characters={"hsf2": "ryu", "sfiii3": "ken"})
    monkeypatch.setattr(sys, "argv", ["motioninput-tui", "--config", str(path), "--game", "sfiii3"])

    assert main() == 0
    assert launched[0].character == "ken"
