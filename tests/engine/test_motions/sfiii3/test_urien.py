"""3rd Strike, Urien. The charge moves, whose timing is read off the decompiled
game: 42 frames in the direction, and it accumulates rather than needing to be
unbroken. See `docs/sfiii3-from-the-decomp.md`."""

from dataclasses import replace

from tests.engine.test_motions.harness import BACK, FORWARD, HK, Script, play_as, press, release

MOVE = "Chariot Tackle"  # charge b then f + K.

# Two 400ms holds of back with 300ms off it in between. Neither half is a charge
# on its own and the stick was let go, but 42 frames were spent holding it.
SPLIT_CHARGE: Script = [
    press(BACK, 0),
    release(BACK, 400),
    press(BACK, 700),
    release(BACK, 1100),
    press(FORWARD, 1140),
    press(HK, 1180),
]

# The same two halves, but let go for longer than the command survives.
LAPSED_CHARGE: Script = [
    press(BACK, 0),
    release(BACK, 400),
    press(BACK, 1200),
    release(BACK, 1600),
    press(FORWARD, 1640),
    press(HK, 1680),
]

WHOLE_CHARGE: Script = [press(BACK, 0), release(BACK, 800), press(FORWARD, 840), press(HK, 880)]


def test_an_unbroken_charge_works(play) -> None:
    assert MOVE in play(WHOLE_CHARGE).moves


def test_a_charge_accumulates_across_a_release(play) -> None:
    """`check_1` counts down while the direction is held and, on release,
    assigns `free2 = free1` - restoring nothing. So the charge is the total time
    spent holding, not the longest unbroken run."""
    assert MOVE in play(SPLIT_CHARGE).moves


def test_letting_go_for_too_long_forgets_the_charge(play) -> None:
    """What does start it over is the command resetting, which takes 42 frames
    of not holding, added up."""
    assert MOVE not in play(LAPSED_CHARGE).moves


def test_a_game_wanting_one_unbroken_hold_refuses_the_split_charge(play) -> None:
    """The accumulation is Third Strike's, not the engine's: with
    `charge_reset_ms` at zero the hold has to be unbroken, which is how every
    game without a decompilation to check is still matched."""
    game = play(SPLIT_CHARGE).session.game
    unbroken = replace(game.ruleset, charge_reset_ms=0)
    assert MOVE not in play_as("sfiii3", "urien", SPLIT_CHARGE, ruleset=unbroken).moves
