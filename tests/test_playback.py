"""A move played back: a script the engine takes, paced by the game's own rules."""

import pytest

from motioninput_tui.controls.buttons import DEFAULT_SET, arrangement
from motioninput_tui.controls.layouts import KB_LEFT, ControlLayout, with_buttons
from motioninput_tui.engine.notation import Button, Direction
from motioninput_tui.games.loader import load_game
from motioninput_tui.games.models import Character, Game, Move
from motioninput_tui.playback import FASTEST_STEP_MS, SETTLE_MS, Run, Timing, beats, plan


def _layout(game: Game) -> ControlLayout:
    """The left-hand keyboard with the game's panel on it, as the app lays it out."""
    buttons = arrangement(game.buttons, slanted_neo_geo=False)
    return KB_LEFT if buttons is DEFAULT_SET else with_buttons(KB_LEFT, buttons)


def _plan(game_key: str, character_key: str, name: str) -> tuple[Game, Character, Move, Timing]:
    game = load_game(game_key)
    character = game.character(character_key)
    move = next(move for move in character.moves if move.name == name)
    return game, character, move, plan(game, character, _layout(game), move)


def _played(game: Game, character: Character, move: Move, timing: Timing) -> Run:
    run = Run(game, character, _layout(game), move, timing)
    run.advance(timing.events[-1].at_ms + SETTLE_MS)
    return run


@pytest.mark.parametrize(
    ("game_key", "character_key", "name"),
    [
        ("sfiii3", "ryu", "Hadou Ken"),  # a quarter circle
        ("sfiii3", "ryu", "Shouryuu Ken"),  # a dragon punch
        ("sfiii3", "ryu", "Shin Shouryuu Ken"),  # a Super Art the trainer has not equipped
        ("sfiii3", "hugo", "Moonsault Press"),  # a 360, finished inside the jump's startup
        ("sfiii3", "hugo", "Gigas Breaker"),  # a 720
        ("sfiii3", "hugo", "Body Press"),  # in the air
        ("sfiii3", "akuma", "Zankuu Hadou Ken"),  # in the air, on the input of one on the ground
        ("sfiii3", "chun-li", "Spinning Bird Kick"),  # a charge, released into a jump
        ("sfiii3", "chun-li", "Hyakuretsu Kyaku"),  # a mash
        ("sfa3", "sakura", "Sakura Otoshi"),  # a special's deliberate taps
        ("sfiii3", "sean", "Shouryuu Cannon"),  # a super's mash, after its cinematic
        ("hsf2", "guile", "Double Flash Kick"),  # a charge with three steps after it
        ("tekken3", "bryan-fury", "Straight Fist"),  # a double tap, forward held for the press
        ("tekken3", "bryan-fury", "One Two"),  # a string, one press after another
        ("tekken3", "bryan-fury", "Quick Kicks"),  # a string on one button, let go between
    ],
)
def test_a_playback_brings_its_move_out(game_key: str, character_key: str, name: str) -> None:
    game, character, move, timing = _plan(game_key, character_key, name)
    assert timing.works
    assert _played(game, character, move, timing).landed


@pytest.mark.parametrize(("game_key", "name"), [("hsf2", "Fireball"), ("sfiii3", "Hadou Ken")])
def test_a_quarter_circle_may_be_as_slow_as_its_games_step_gap(game_key: str, name: str) -> None:
    """Super Turbo's is 140ms, Third Strike's the ten frames read off the decompilation: the search finds each."""
    game, _, _, timing = _plan(game_key, "ryu", name)
    assert timing.slowest_ms == game.ruleset.step_gap_ms


def test_the_step_played_is_halfway_between_a_frame_and_the_slowest() -> None:
    *_, timing = _plan("sfiii3", "ryu", "Hadou Ken")
    assert timing.slowest_ms is not None
    assert timing.step_ms == (FASTEST_STEP_MS + timing.slowest_ms) // 2


def test_beats_are_the_directions_and_the_button_as_they_are_pressed() -> None:
    game, _, _, timing = _plan("sfiii3", "ryu", "Hadou Ken")
    step = timing.step_ms
    assert beats(timing, _layout(game)) == [
        (0, Direction.DOWN),
        (step, Direction.DOWN_FORWARD),
        (2 * step, Direction.FORWARD),
        (2 * step + step // 2, (Button.LP,)),
    ]


def test_a_720_is_two_270s_as_a_leverless_does_it() -> None:
    """Forward round to up, twice, up snapping straight back to forward: all four cardinals each time."""
    game, _, _, timing = _plan("sfiii3", "hugo", "Gigas Breaker")
    circle = [
        Direction.FORWARD,
        Direction.DOWN_FORWARD,
        Direction.DOWN,
        Direction.DOWN_BACK,
        Direction.BACK,
        Direction.UP_BACK,
        Direction.UP,
    ]
    assert [beat for _, beat in beats(timing, _layout(game)) if isinstance(beat, Direction)] == circle * 2


def test_a_move_no_timing_brings_out_says_what_comes_out_instead() -> None:
    """Gill's Cryo-kinesis is Pyro-kinesis from the other side, and the trainer has no sides."""
    *_, timing = _plan("sfiii3", "gill", "Cryo-kinesis")
    assert not timing.works
    assert timing.instead == ("Pyro-kinesis",)


def test_a_playback_goes_the_same_however_its_clock_is_driven() -> None:
    """The screen advances it a frame at a time, the search in one go, and the two have to agree."""
    game, character, move, timing = _plan("sfiii3", "hugo", "Moonsault Press")
    end = timing.events[-1].at_ms + SETTLE_MS
    whole = _played(game, character, move, timing)
    stepped = Run(game, character, _layout(game), move, timing)
    for to_ms in range(-50, end, 17):
        stepped.advance(to_ms)
    stepped.advance(end)
    assert stepped.landed
    assert [(entry.direction, entry.at_ms) for entry in stepped.session.entries] == [
        (entry.direction, entry.at_ms) for entry in whole.session.entries
    ]
