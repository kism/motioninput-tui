"""Config persistence: what survives a save/load round trip, and what is dropped."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from motioninput_tui.config import Config

if TYPE_CHECKING:
    from pathlib import Path


def test_gamepad_bindings_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    Config(gamepad_bindings={"HP": "pad:1", "MK": "pad:5"}, path=path).save()
    assert Config.load(path).gamepad_bindings == {"HP": "pad:1", "MK": "pad:5"}


def test_malformed_gamepad_bindings_load_as_empty(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                "gamepad_bindings": {
                    "HP": "pad:1",  # kept
                    "LP": "mouse3",  # dropped: not a pad code
                    "MK": 4,  # dropped: not a string
                }
            }
        )
    )
    assert Config.load(path).gamepad_bindings == {"HP": "pad:1"}


def test_gamepad_bindings_default_to_empty(tmp_path: Path) -> None:
    assert Config.load(tmp_path / "missing.json").gamepad_bindings == {}
