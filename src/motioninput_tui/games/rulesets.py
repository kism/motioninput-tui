"""Per-game metadata and input rules.

The headline difference between these games is the dragon punch. Third Strike
will give you one for holding down and double tapping forward; Super Turbo and
Alpha 3 want a real f,d,df and will hand you a fireball if they do not get it.
"""

from __future__ import annotations

from dataclasses import dataclass

from motioninput_tui.engine.ruleset import Ruleset


@dataclass(frozen=True, slots=True)
class GameSpec:
    """Everything about a game except its roster, which is loaded from data."""

    key: str
    name: str
    short_name: str
    ruleset: Ruleset
    notes: tuple[str, ...]
    reference: str


HSF2 = GameSpec(
    key="hsf2",
    name="Hyper Street Fighter II: The Anniversary Edition",
    short_name="HSF2",
    ruleset=Ruleset(
        motion_window_ms=250,
        activation_window_ms=120,
        max_intermediate=1,
        tail_states=2,
        lenient_diagonals=False,
        charge_ms=950,
        charge_release_ms=180,
        dp_double_tap=False,
        dp_skip_down=False,
        negative_edge=False,
        mash_count=5,
        rotation_window_ms=450,
        rotation_slack=2,
    ),
    notes=(
        "Strictest of the three. Motions must be clean and diagonals cannot be skipped.",
        "No dragon punch shortcut: holding down and tapping forward gives you nothing.",
        "No negative edge, so releasing a button never triggers a special.",
        "Charges are long, around 55 frames.",
    ),
    reference="references/hsf2.txt",
)

SFA3 = GameSpec(
    key="sfa3",
    name="Street Fighter Alpha 3",
    short_name="SFA3",
    ruleset=Ruleset(
        motion_window_ms=300,
        activation_window_ms=150,
        max_intermediate=1,
        tail_states=2,
        lenient_diagonals=False,
        charge_ms=880,
        charge_release_ms=200,
        dp_double_tap=False,
        dp_skip_down=False,
        negative_edge=True,
        mash_count=5,
        rotation_window_ms=500,
        rotation_slack=2,
    ),
    notes=(
        "A little more forgiving than SF2, but still wants the full f,d,df for a dragon punch.",
        "Negative edge exists, so a released button can complete a special.",
        "Diagonals still matter: d,f is a fireball, not a shortcut to anything else.",
    ),
    reference="references/sfa3.txt",
)

SFIII3 = GameSpec(
    key="sfiii3",
    name="Street Fighter III: 3rd Strike",
    short_name="SFIII:3S",
    ruleset=Ruleset(
        motion_window_ms=420,
        activation_window_ms=220,
        max_intermediate=2,
        tail_states=3,
        lenient_diagonals=True,
        charge_ms=800,
        charge_release_ms=250,
        dp_double_tap=True,
        dp_skip_down=True,
        negative_edge=True,
        mash_count=4,
        rotation_window_ms=600,
        rotation_slack=3,
    ),
    notes=(
        "The lenient one. Hold down and double tap forward and you get a dragon punch.",
        "Diagonals can be skipped, so d,f still reads as a quarter circle.",
        "Wider motion windows and more tolerance for junk inputs mid-motion.",
        "Negative edge exists.",
    ),
    reference="references/sfiii3.txt",
)

GAME_SPECS: dict[str, GameSpec] = {spec.key: spec for spec in (HSF2, SFA3, SFIII3)}
DEFAULT_GAME = SFIII3.key


def get_spec(key: str) -> GameSpec:
    """Look up a game spec by key."""
    try:
        return GAME_SPECS[key]
    except KeyError:
        known = ", ".join(GAME_SPECS)
        message = f"Unknown game {key!r}. Known games: {known}"
        raise KeyError(message) from None
