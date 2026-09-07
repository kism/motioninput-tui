"""Motion recognition, driven at the key level with explicit timestamps.

Everything here goes through the real input source, so the tests cover SOCD
cleaning and the direction states it produces as well as the matchers.
``exact_input=True`` means key releases are reported, as they are in a terminal
speaking the kitty keyboard protocol, so no auto-repeat has to be simulated.
"""

from __future__ import annotations

import pytest

from motioninput_tui.controls.layouts import HITBOX
from motioninput_tui.engine.session import TrainingSession
from motioninput_tui.games.loader import load_game

# Hitbox: a is back, s is down, d is forward, space is up. Attacks on u i o / j k l.
BACK, DOWN, FORWARD, UP = "a", "s", "d", "space"
MK, HK, HP = "k", "l", "o"

TICK_MS = 8


def play(game_key: str, character_key: str, script: list[tuple[str, str, int]]) -> TrainingSession:
    """Run a script of (action, key, at_ms) through a session.

    ``action`` is "down" or "up". Time is advanced in small steps between
    events so hold expiry runs the way it does under the live interface.
    """
    game = load_game(game_key)
    session = TrainingSession(game, game.character(character_key), HITBOX, exact_input=True)
    now = 0
    for action, key, at_ms in script:
        while now < at_ms:
            now = min(now + TICK_MS, at_ms)
            session.tick(now)
        if action == "down":
            session.press(key, at_ms)
        else:
            session.release(key, at_ms)
    for _ in range(20):
        now += TICK_MS
        session.tick(now)
    return session


def directions(session: TrainingSession) -> str:
    """The input strip as arrows, for readable assertions."""
    return " ".join(entry.direction.glyph for entry in session.entries)


def moves(session: TrainingSession) -> list[str]:
    """Activated moves, oldest first."""
    return [activation.name for activation in session.activations][::-1]


# Back, then add down, then add forward. Pressing forward while back is still
# held gives down-forward straight away, so a plain down never appears. This is
# an ordinary hitbox half circle and the game accepts it.
HALF_CIRCLE_WITHOUT_DOWN = [
    ("down", BACK, 0),
    ("down", DOWN, 60),
    ("down", FORWARD, 120),
    ("up", DOWN, 180),
    ("up", BACK, 185),
    ("down", MK, 220),
]


def test_half_circle_skipping_down_makes_the_expected_directions() -> None:
    session = play("sfiii3", "elena", HALF_CIRCLE_WITHOUT_DOWN)
    assert directions(session) == "← ↙ ↘ →"


def test_half_circle_forward_activates_when_down_alone_is_skipped() -> None:
    session = play("sfiii3", "elena", HALF_CIRCLE_WITHOUT_DOWN)
    assert "Rhino Horn" in moves(session)


def test_half_circle_forward_activates_when_down_is_hit() -> None:
    """The same move, done passing cleanly through every direction."""
    session = play(
        "sfiii3",
        "elena",
        [
            ("down", BACK, 0),
            ("down", DOWN, 60),
            ("up", BACK, 100),
            ("down", FORWARD, 140),
            ("up", DOWN, 180),
            ("down", MK, 220),
        ],
    )
    assert directions(session) == "← ↙ ↓ ↘ →"
    assert "Rhino Horn" in moves(session)


def test_back_to_forward_is_not_a_half_circle() -> None:
    """Walking back then forward must not count as a half circle."""
    session = play(
        "sfiii3",
        "elena",
        [("down", BACK, 0), ("up", BACK, 60), ("down", FORWARD, 120), ("down", MK, 160)],
    )
    assert "Rhino Horn" not in moves(session)


def test_quarter_circle_is_not_a_half_circle() -> None:
    """A quarter circle forward has no back in it, so it stays a quarter circle."""
    session = play(
        "sfiii3",
        "elena",
        [
            ("down", DOWN, 0),
            ("down", FORWARD, 70),
            ("up", DOWN, 110),
            ("down", HK, 150),
        ],
    )
    assert "Rhino Horn" not in moves(session)


@pytest.mark.parametrize(
    ("game_key", "character_key", "move_name"),
    [("sfiii3", "ryu", "Hadou Ken"), ("sfa3", "ryu", "Hadou Ken"), ("hsf2", "ryu", "Fireball")],
)
def test_quarter_circle_forward(game_key: str, character_key: str, move_name: str) -> None:
    session = play(
        game_key,
        character_key,
        [("down", DOWN, 0), ("down", FORWARD, 70), ("up", DOWN, 110), ("down", HP, 150)],
    )
    assert moves(session) == [move_name]


@pytest.mark.parametrize(
    ("game_key", "expected"),
    [("sfiii3", "Shouryuu Ken"), ("sfa3", None), ("hsf2", None)],
)
def test_hold_down_double_tap_forward_is_a_dragon_punch_only_in_third_strike(
    game_key: str, expected: str | None
) -> None:
    """The headline difference between the games."""
    session = play(
        game_key,
        "ryu",
        [
            ("down", DOWN, 0),
            ("down", FORWARD, 80),
            ("up", FORWARD, 150),
            ("down", FORWARD, 230),
            ("down", HP, 270),
        ],
    )
    if expected is None:
        assert moves(session) == []
    else:
        assert expected in moves(session)
