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


def test_a_game_renamed_to_its_mame_set_migrates(tmp_path: Path) -> None:
    """The remembered character comes along with the game."""
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"game": "ssii", "characters": {"ssii": "galford", "lb2": "yuki"}}))
    config = Config.load(path)
    assert (config.game, config.characters) == ("samsho2", {"samsho2": "galford", "lastbld2": "yuki"})


def test_settings_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    Config(neo_geo_slant=True, path=path).save()
    assert Config.load(path).neo_geo_slant is True


def test_a_malformed_setting_falls_back_to_its_default(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"neo_geo_slant": "sure"}))
    assert Config.load(path).neo_geo_slant is False


def test_notation_round_trips(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    Config(notation={"dragon": "kanji"}, path=path).save()
    assert Config.load(path).notation == {"dragon": "kanji"}


def test_a_notation_style_that_no_longer_exists_is_dropped(tmp_path: Path) -> None:
    """Styles come and go as the menu grows; a stale one must not draw nothing."""
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"notation": {"dragon": "kanji", "quarter": "sharpie", "nonsense": "arrows"}}))
    assert Config.load(path).notation == {"dragon": "kanji"}


def test_the_character_is_remembered_per_game(tmp_path: Path) -> None:
    """Switching game and back returns to whoever was being trained on it."""
    path = tmp_path / "config.json"
    Config(game="sfiii3", character="ken", path=path).save()

    config = Config.load(path)
    config.game, config.character = "sfa3", "sakura"
    config.save()

    assert Config.load(path).characters == {"sfiii3": "ken", "sfa3": "sakura"}


def test_malformed_per_game_characters_are_dropped(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"characters": {"sfiii3": "ken", "sfa3": 4, "": "ryu", "hsf2": ""}}))
    assert Config.load(path).characters == {"sfiii3": "ken"}
