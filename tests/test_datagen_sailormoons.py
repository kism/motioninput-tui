"""The S roster, taken out of a guide that documents two games at once.

The reference is a quick reference for Sailor Moon S *and* its SuperS sequel
folded together, tagging the entries that belong to only one of them. Getting
that filter wrong does not look like a bug: the roster still loads and the
characters are all present, and a move belonging to the sequel reads exactly
like one that does not until somebody plays the game and cannot find it.

Two of the guide's own habits made that filter harder than a prefix check, and
both are regression-tested here: it runs a character's two desperations together
with no blank line between them, one per game, and its asides nest and run to
whole paragraphs.
"""

from motioninput_tui.games.loader import INPUT_DISPLAY, load_game

GAME = "sailormoons"


def _roster_keys() -> set[str]:
    return {character.key for character in load_game(GAME).characters} - {INPUT_DISPLAY}


def _move_names(character_key: str) -> set[str]:
    return {move.name for move in load_game(GAME).character(character_key).moves}


def test_the_sequel_only_character_is_left_out() -> None:
    """Sailor Saturn's own heading marks her as being in the sequel alone."""
    assert "sailor-saturn" not in _roster_keys()


def test_the_roster_is_the_nine_this_game_has() -> None:
    assert len(_roster_keys()) == 9  # ruff: ignore[magic-value-comparison]


def test_a_move_the_sequel_alone_has_is_left_out() -> None:
    names = _move_names("sailor-moon")
    assert "Moon Gorgeous Meditation" not in names
    assert "Moon Spiral Heart Attack" in names


def test_two_desperations_run_together_are_split_by_game() -> None:
    """The guide gives this character one desperation per game with no blank
    line between them, so reflowing on blank lines alone merged the pair: the
    move this game has was lost and took the sequel's name and input with it."""
    names = _move_names("sailor-chibi-moon")
    assert "Luna-P Attack" in names
    assert "Twinkle Yell" not in names


def test_an_aside_does_not_leak_into_the_command() -> None:
    """This one's commentary nests brackets and runs to a paragraph, so pairing
    them off left the prose between the inner and outer closers in the command -
    where the move list would have shown it to the player."""
    move = next(m for m in load_game(GAME).character("sailor-jupiter").moves if m.name == "Jupiter Double Axle")
    assert move.command == "D DT T + Strong Kick or Kick"
