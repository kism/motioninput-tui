"""Chains: a move that follows on from another, and is only live once it has come out.

The per-character files under ``tests/engine/test_motions`` show what a chain
gives you at the keys; this is about the shape of the data and the one rule the
engine enforces over every roster at once.
"""

import pytest

from motioninput_tui.engine.recognizer import Recognizer
from motioninput_tui.games.loader import load_game
from motioninput_tui.games.rulesets import GAME_SPECS

CHAINED_GAMES = (
    "kof98",
    "kof2001",
    "lastbld2",
    "martmast",
    "samsh5sp",
    "samsho2",
    "sfa3",
    "sfiii3",
    "tekken3",
    "usfiv",
)
"""The rosters whose guides say which move a link comes out of. The rest write
it in prose the parsers cannot follow, so their links stay struck through."""


@pytest.mark.parametrize("key", GAME_SPECS)
def test_every_link_names_a_move_its_character_has(key: str) -> None:
    """A parent that is not in the roster would be a link to nothing: the move
    would sit in the list looking trainable and never come out."""
    game = load_game(key)
    for character in game.characters:
        names = {move.name for move in character.moves}
        for move in character.moves:
            if move.follows:
                assert move.follows in names, f"{key}/{character.key}: {move.name} follows {move.follows!r}"


@pytest.mark.parametrize("key", GAME_SPECS)
def test_a_link_never_matches_on_its_own(key: str) -> None:
    """The point of the whole mechanism. A link's motion is usually one the
    character already has - Master Huang's Heavy Axe is a plain quarter circle,
    and so is his Grasshopper - so a link left in the always-live ranking would
    take moves off the move it is supposed to follow.

    Compared by identity, not by name: a guide can give a link the same name as
    a standalone move (Master Huang has a Drill Kick of each), and those are two
    different moves that have to be treated differently."""
    game = load_game(key)
    for character in game.characters:
        recognizer = Recognizer(character.moves, game.ruleset)
        ranked = {id(move) for move in recognizer._ranked}
        for move in character.moves:
            if move.follows:
                assert id(move) not in ranked, f"{key}/{character.key}: {move.name} is live without its parent"


@pytest.mark.parametrize("key", CHAINED_GAMES)
def test_the_wired_games_actually_have_chains(key: str) -> None:
    """Guards the parsers: a change that stopped finding parents would other-
    wise just quietly go back to striking every link through."""
    game = load_game(key)
    assert sum(1 for c in game.characters for m in c.moves if m.follows) > 0
    assert game.ruleset.chain_window_ms > 0, "a roster with chains needs a window for them to open in"


@pytest.mark.parametrize("key", GAME_SPECS)
def test_a_game_without_a_window_has_no_chains(key: str) -> None:
    """The two go together: links are unreachable without a window, so a roster
    carrying them and no window would be listing moves it never gives you."""
    game = load_game(key)
    if game.ruleset.chain_window_ms:
        return
    assert not [m for c in game.characters for m in c.moves if m.follows]


def test_a_chain_does_not_loop() -> None:
    """A link that leads back to its own parent would keep itself open forever."""
    for key in GAME_SPECS:
        for character in load_game(key).characters:
            parents = {move.name: move.follows for move in character.moves if move.follows}
            for name, first in parents.items():
                seen, at = {name}, first
                while at in parents:
                    assert at not in seen, f"{key}/{character.key}: {name} chains in a circle"
                    seen.add(at)
                    at = parents[at]
