"""The setup screen's character list: the input display, then alphabetical, whatever order the roster is in."""

from motioninput_tui.games.loader import load_game
from motioninput_tui.tui.screens.setup import _ordered_characters


def test_characters_are_sorted_by_display_name() -> None:
    game = load_game("kof98")
    first, *names = [character.name for character in _ordered_characters(game)]

    assert first == "Input display"
    assert names == sorted(names, key=str.casefold)
    assert names != [character.name for character in game.characters[1:]]  # the roster itself is not sorted
