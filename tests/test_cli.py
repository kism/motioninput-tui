"""Startup decisions made before the interface takes over the terminal."""

import json
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from motioninput_tui.__main__ import main
from motioninput_tui.games.loader import GameDataMissingError

if TYPE_CHECKING:
    from motioninput_tui.config import Config

ARGPARSE_USAGE_ERROR = 2
"""What argparse exits with when it does not recognise an option."""


def _raise_missing(_key: str) -> None:
    raise GameDataMissingError(Path("games/data/sfiii3.json"))


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


def test_missing_game_data_stops_the_app_starting(saved, launched, monkeypatch) -> None:
    """The one selection problem there is no falling back from: a character can
    be dropped and the picker opens, but an absent roster leaves nothing to do."""
    path = saved(game="sfiii3", character="ken")
    monkeypatch.setattr("motioninput_tui.__main__.load_game", _raise_missing)

    monkeypatch.setattr(sys, "argv", ["motioninput-tui", "--config", str(path)])
    assert main() == 1
    assert launched == []


@pytest.mark.parametrize("flag", ["--game", "--character", "--layout", "--loose-buffer", "--no-key-release"])
def test_what_to_train_is_not_a_command_line_option(flag: str, saved, monkeypatch) -> None:
    """These all used to exist and were removed: the config file is the one place
    the selection lives, so there is no second way to say it and no precedence
    rule between them. Argparse rejects an unknown option rather than ignoring
    it, so anyone still passing one is told, not quietly given the defaults."""
    path = saved(game="sfiii3", character="ken")
    monkeypatch.setattr(sys, "argv", ["motioninput-tui", "--config", str(path), flag, "sfiii3"])

    with pytest.raises(SystemExit) as exit_info:
        main()
    assert exit_info.value.code == ARGPARSE_USAGE_ERROR


def test_the_whole_command_line_is_these_five(capsys, monkeypatch) -> None:
    """A guard on the surface itself, since flags regrow one convenience at a
    time. Anything added here is a deliberate decision to reopen that door."""
    monkeypatch.setattr(sys, "argv", ["motioninput-tui", "--help"])
    with pytest.raises(SystemExit):
        main()

    usage = capsys.readouterr().out.split("Fighting game")[0]
    # Every option argparse prints, taken from inside the usage brackets so the
    # program's own name cannot be mistaken for one.
    assert set(re.findall(r"\[(-{1,2}[a-z][a-z-]*)", usage)) == {
        "-h",
        "--config",
        "--list",
        "--check-terminal",
        "--version",
        "-v",
    }
