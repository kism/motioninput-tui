"""Config persistence: what survives a save/load round trip, and what is dropped."""

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


def test_keyboard_bindings_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    Config(keyboard_bindings={"HP": "semicolon", "up": "w"}, path=path).save()
    assert Config.load(path).keyboard_bindings == {"HP": "semicolon", "up": "w"}


def test_malformed_keyboard_bindings_are_dropped(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"keyboard_bindings": {"HP": "j", "nonsense": "q", "MP": "", "LK": 4}}))
    assert Config.load(path).keyboard_bindings == {"HP": "j"}


def test_a_replaced_keyboard_layout_migrates(tmp_path: Path) -> None:
    """A config from before the keyboard layouts changed still opens somewhere."""
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"layout": "hitbox"}))
    assert Config.load(path).layout == "keyboard-left"
    path.write_text(json.dumps({"layout": "southpaw"}))
    assert Config.load(path).layout == "keyboard-right"


def test_settings_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    Config(lenient_half_circles=False, path=path).save()
    assert Config.load(path).lenient_half_circles is False


def test_a_malformed_setting_falls_back_to_its_default(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"lenient_half_circles": "sure"}))
    assert Config.load(path).lenient_half_circles is True


def test_settings_default_to_relaxed(tmp_path: Path) -> None:
    assert Config.load(tmp_path / "missing.json").lenient_half_circles is True


def test_notation_round_trips(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    Config(notation={"dragon": "kanji"}, path=path).save()
    assert Config.load(path).notation == {"dragon": "kanji"}


def test_a_notation_style_that_no_longer_exists_is_dropped(tmp_path: Path) -> None:
    """Styles come and go as the menu grows; a stale one must not draw nothing."""
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"notation": {"dragon": "kanji", "quarter": "sharpie", "nonsense": "arrows"}}))
    assert Config.load(path).notation == {"dragon": "kanji"}
