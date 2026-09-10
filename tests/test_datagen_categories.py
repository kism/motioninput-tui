"""Move categories, and how each KoF guide says a move is a super.

Both guides name the group outright under a `SUPER MOVES` heading, so the
parsers read the category off the guide and nothing has to be inferred from a
motion or from where a move sits in a list.
"""

from motioninput_tui.games.loader import load_game
from motioninput_tui.games.models import Category


def test_98_takes_the_category_from_the_guides_own_heading() -> None:
    """Yuri's DMs sit under `SUPER MOVES`; her fireball does not."""
    yuri = {move.name: move for move in load_game("kof98").character("yuri-sakazaki").moves}
    assert yuri["Hien Hou'ou Kyaku"].category == Category.SUPER
    assert yuri["Hien Rekkou"].category == Category.SUPER
    assert yuri["Ko ou Ken"].category == Category.SPECIAL


def test_2001_takes_the_category_from_the_guides_own_heading() -> None:
    """Yuri's two DMs sit under `SUPER MOVES`; her command grab does not."""
    yuri = {move.name: move for move in load_game("kof2001").character("yuri-sakazaki").moves}
    assert yuri["Hien Hou'ou Kyaku (DM)"].category == Category.SUPER
    assert yuri["Hien Hou'ou Kyaku (SDM)"].category == Category.SUPER
    assert yuri["Hyakuretsu Binta"].category == Category.SPECIAL
    assert yuri["Ko Ou Ken"].category == Category.SPECIAL


def test_neither_kof_roster_leaves_a_move_uncategorised() -> None:
    """Every move is under one of the four headings, so none falls back to OTHER.

    This is the headline difference from the guides these two replaced, where a
    third of the 2001 roster had no category the parser could work out.
    """
    uncategorised = [
        (game_key, character.key, move.name)
        for game_key in ("kof98", "kof2001")
        for character in load_game(game_key).characters
        for move in character.moves
        if move.category == Category.OTHER
    ]
    assert uncategorised == []
