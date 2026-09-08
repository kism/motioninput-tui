"""The global settings: what they change in the engine, and how they are stored.

Relaxed half circles is the one that changes matching, so it is checked against
the same scripts the Elena tests use: one hitbox half circle that never touches
straight down, and one that rolls cleanly through it.
"""

from __future__ import annotations

from dataclasses import replace

from motioninput_tui.config import Config
from motioninput_tui.engine.recognizer import BufferPolicy
from motioninput_tui.engine.ruleset import Ruleset
from motioninput_tui.games.loader import load_game
from motioninput_tui.settings import SETTINGS, current, tuned_game
from tests.engine.test_motions.harness import (
    HALF_CIRCLE_SKIPPING_DOWN_MK,
    HALF_CIRCLE_THROUGH_DOWN_MK,
    play_as,
)

GAME, CHARACTER, MOVE = "sfiii3", "elena", "Rhino Horn"


def rules(*, relaxed: bool) -> Ruleset:
    """3rd Strike's rules with the half circle setting either way."""
    return tuned_game(load_game(GAME), Config(lenient_half_circles=relaxed)).ruleset


def test_relaxed_half_circles_take_one_that_skips_the_down() -> None:
    relaxed = rules(relaxed=True)
    assert MOVE in play_as(GAME, CHARACTER, HALF_CIRCLE_SKIPPING_DOWN_MK, ruleset=relaxed).moves


def test_strict_half_circles_want_the_down() -> None:
    assert MOVE not in play_as(GAME, CHARACTER, HALF_CIRCLE_SKIPPING_DOWN_MK, ruleset=rules(relaxed=False)).moves


def test_strict_half_circles_still_take_a_clean_one() -> None:
    """Turning the relaxation off must not make the real motion unusable."""
    assert MOVE in play_as(GAME, CHARACTER, HALF_CIRCLE_THROUGH_DOWN_MK, ruleset=rules(relaxed=False)).moves


def test_tuning_leaves_the_rest_of_the_game_alone() -> None:
    """Only the player's own settings may differ from what the game says."""
    game = load_game(GAME)
    tuned = tuned_game(game, Config(lenient_half_circles=False))
    assert tuned == replace(game, ruleset=replace(game.ruleset, lenient_half_circles=False))


def test_loose_buffer_reads_and_writes_the_policy() -> None:
    """The pane sees every setting as a boolean, including the one that is an enum."""
    config = Config()
    assert config.loose_buffer is False
    config.loose_buffer = True
    assert config.buffer_policy is BufferPolicy.LOOSE
    config.loose_buffer = False
    assert config.buffer_policy is BufferPolicy.CONSUME


def test_every_setting_is_a_boolean_on_the_config() -> None:
    """The settings pane writes them back by name, so they have to be there."""
    values = current(Config())
    assert set(values) == {setting.attribute for setting in SETTINGS}
    assert all(isinstance(value, bool) for value in values.values())
