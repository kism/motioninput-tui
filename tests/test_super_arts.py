"""Super Arts: 3rd Strike tags its supers I/II/III, and only one is live at a time."""

import pytest

from motioninput_tui.controls.layouts import HITBOX, with_buttons
from motioninput_tui.engine.session import TrainingSession
from motioninput_tui.games.loader import load_game


def _session(game_key: str, character_key: str) -> TrainingSession:
    game = load_game(game_key)
    character = game.character(character_key)
    return TrainingSession(game, character, with_buttons(HITBOX, game.buttons), exact_input=True)


def test_third_strike_supers_are_tagged() -> None:
    """The guide's I/II/III flag survives datagen and groups the supers."""
    sean = load_game("sfiii3").character("sean")

    assert sean.super_arts == ("I", "II", "III")
    assert {move.name: move.super_art for move in sean.moves if move.super_art} == {
        "Hadou Burst": "I",
        "Shouryuu Cannon": "II",
        "Hyper Tornado": "III",
    }


def test_a_super_art_can_hold_more_than_one_move() -> None:
    """Akuma's ground and air Messatsu share SA I; Q's SA III keeps its follow-ups."""
    game = load_game("sfiii3")

    akuma = {move.name for move in game.character("akuma").moves if move.super_art == "I"}
    assert akuma == {"Messatsu Gou Hadou", "Tenma Gou Zankuu"}

    q_super_art_three = [move.name for move in game.character("q").moves if move.super_art == "III"]
    assert len(q_super_art_three) == len(["the super", "its Dageki follow-up", "its Hokaku follow-up"])


@pytest.mark.parametrize("game_key", ["hsf2", "sfa3", "kof98"])
def test_only_third_strike_has_super_arts(game_key: str) -> None:
    """Everywhere else every super is always available, so there is nothing to pick."""
    game = load_game(game_key)

    assert all(not character.super_arts for character in game.characters)


def test_the_session_starts_on_the_first_super_art() -> None:
    session = _session("sfiii3", "sean")

    assert session.super_arts == ("I", "II", "III")
    assert session.super_art == "I"
    live = {move.name for move in session.recognizer.moves}
    assert "Hadou Burst" in live
    assert "Shouryuu Cannon" not in live


def test_selecting_a_super_art_swaps_which_one_is_live() -> None:
    session = _session("sfiii3", "sean")

    session.select_super_art("II")

    assert session.super_art == "II"
    live = {move.name for move in session.recognizer.moves}
    assert "Shouryuu Cannon" in live
    assert "Hadou Burst" not in live
    # Non-supers are untouched by the choice.
    assert "Dragon Smash" in live


def test_a_game_without_super_arts_keeps_every_move() -> None:
    session = _session("hsf2", "ryu")

    assert session.super_arts == ()
    assert not session.super_art
    assert len(session.recognizer.moves) == len(session.character.moves)
