"""Move categories, and the KoF DM/SDM block in particular.

Both KoF guides list a character's DMs and SDMs as the last blank-line group of
the move list. `super_tail` is what turns that grouping into `Category.SUPER`,
so Yuri's ``2363214+K`` HIEN HOU'OU KYAKU reads as a super while her
``632146+K`` Hyakuretsu Binta, a command grab, stays a special.
"""

from motioninput_tui.games.loader import load_game
from motioninput_tui.games.models import Category, Move
from motioninput_tui_datagen.common import super_tail


def _move(name: str, command: str) -> Move:
    return Move(name=name, command=command, category=Category.SPECIAL)


def test_super_tail_tags_only_the_last_group() -> None:
    specials = [_move("Ko'ou Ken", "236+P"), _move("Hyakuretsu Binta", "632146+K")]
    supers = [_move("Shin! Chou Upper", "236236+K"), _move("HIEN HOU'OU KYAKU", "2363214+K")]
    result = super_tail([specials, supers])
    assert [move.category for move in result] == [
        Category.SPECIAL,
        Category.SPECIAL,
        Category.SUPER,
        Category.SUPER,
    ]


def test_super_tail_skips_empty_groups() -> None:
    result = super_tail([[_move("a", "236+P")], [], [_move("b", "2363214+P")], []])
    assert [move.category for move in result] == [Category.SPECIAL, Category.SUPER]


def test_super_tail_leaves_a_lone_group_alone() -> None:
    """A character with no separate DM block should not read as all supers."""
    only = [_move("a", "236+P"), _move("b", "236+K")]
    assert super_tail([only]) == only


def test_kof_desperation_moves_are_supers_in_the_generated_rosters() -> None:
    yuri = load_game("kof2001").character("yuri-sakazaki")
    by_name = {move.name: move for move in yuri.moves}
    assert by_name["HIEN HOU'OU KYAKU"].category == Category.SUPER
    assert by_name["Shin! Chou Upper"].category == Category.SUPER
    assert by_name["Hyakuretsu Binta"].category == Category.SPECIAL  # a command grab, one group up


def test_a_shared_motion_is_split_by_the_block_it_sits_in() -> None:
    """``632146`` is Goro's Tenchi Gaeshi (special) and Athena's PSYCHIC 9 (a DM)."""
    game = load_game("kof2001")
    goro = {move.name: move for move in game.character("goro-daimon").moves}
    athena = {move.name: move for move in game.character("athena-asamiya").moves}
    assert goro["Tenchi Gaeshi"].category == Category.SPECIAL
    assert athena["PSYCHIC 9"].category == Category.SUPER
