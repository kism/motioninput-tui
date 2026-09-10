"""3rd Strike, Chun-Li. The Hyakuretsu Kyaku, which is the game's only move
matched by mashing rather than by a motion.

`check_4` in the decompilation keeps three counters, one per button strength,
and fires when any one of them reaches five. See
`docs/sfiii3-from-the-decomp.md`.
"""

from dataclasses import replace

from tests.engine.test_motions.harness import HK, LK, MK, play_as, press, release, taps

MOVE = "Hyakuretsu Kyaku"


def rolled_kicks(gap_ms: int = 120) -> list:
    """Five presses spread across all three kicks, one after another."""
    return [
        event
        for index, key in enumerate((LK, MK, HK, LK, MK))
        for event in (press(key, index * gap_ms), release(key, index * gap_ms + 40))
    ]


def test_five_presses_of_one_kick_is_the_hyakuretsu(play) -> None:
    assert play(taps(MK, 0, 5, gap_ms=120)).moves == [MOVE]


def test_four_is_not_enough(play) -> None:
    assert play(taps(MK, 0, 4, gap_ms=120)).moves == []


def test_rolling_across_the_kicks_is_not_a_mash(play) -> None:
    """Five presses, but two, two and one across the three counters, so none of
    them reaches five. Piano-ing the kicks does not start it."""
    assert play(rolled_kicks()).moves == []


def test_the_presses_may_be_spread_over_the_whole_window(play) -> None:
    """Ninety-nine frames, which is a good deal slower than mashing."""
    assert play(taps(MK, 0, 5, gap_ms=400)).moves == [MOVE]


def test_a_game_counting_any_button_takes_the_rolled_kicks() -> None:
    """The one-counter-per-button rule is 3rd Strike's, not the engine's: with
    `mash_same_button` off, every press of a button the move accepts counts,
    which is how the games with nothing to check against are still matched."""
    game_rules = play_as("sfiii3", "chun-li", []).session.game.ruleset
    lenient = replace(game_rules, mash_same_button=False)
    assert MOVE in play_as("sfiii3", "chun-li", rolled_kicks(), ruleset=lenient).moves
