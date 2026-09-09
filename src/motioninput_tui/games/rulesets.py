"""Per-game metadata and input rules.

The headline difference between these games is the dragon punch. Third Strike
will give you one for holding down and double tapping forward; Super Turbo and
Alpha 3 want a real f,d,df and will hand you a fireball if they do not get it.
"""

from dataclasses import dataclass

from motioninput_tui.controls.buttons import NEO_GEO, STREET_FIGHTER, ButtonSet
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
    buttons: ButtonSet = STREET_FIGHTER
    """The panel this game is played on. See :mod:`motioninput_tui.controls.buttons`."""


HSF2 = GameSpec(
    key="hsf2",
    name="Hyper Street Fighter II",
    short_name="HSF2",
    ruleset=Ruleset(
        motion_window_ms=250,
        activation_window_ms=120,
        step_gap_ms=140,
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
        step_gap_ms=170,
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
        step_gap_ms=210,
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

KOF98 = GameSpec(
    key="kof98",
    name="The King of Fighters '98",
    short_name="KoF '98",
    ruleset=Ruleset(
        motion_window_ms=320,
        activation_window_ms=160,
        step_gap_ms=180,
        max_intermediate=1,
        tail_states=2,
        lenient_diagonals=True,
        charge_ms=850,
        charge_release_ms=220,
        dp_double_tap=False,
        dp_skip_down=False,
        negative_edge=True,
        mash_count=5,
        rotation_window_ms=500,
        rotation_slack=2,
    ),
    notes=(
        "Neo Geo four-button panel: A and B are the light punch and kick, C and D the heavy pair.",
        "SNK buffering is generous, so a quarter circle done as down, forward still comes out.",
        "No dragon punch shortcut: f,d,df means f,d,df, and holding down then tapping forward gives nothing.",
        "Negative edge exists, so releasing a button can complete a special.",
        "Charge moves want most of a second in the held direction.",
    ),
    reference="references/kof98.txt",
    buttons=NEO_GEO,
)

KOF2001 = GameSpec(
    key="kof2001",
    name="The King of Fighters 2001",
    short_name="KoF 2001",
    ruleset=Ruleset(
        # Mechanically this is KoF '98 three years on, so the fields track it.
        # The Eolith/BrezzaSoft engine is reckoned a touch looser and slower to
        # respond, which is the only reason the windows are a hair wider.
        motion_window_ms=330,
        activation_window_ms=170,
        step_gap_ms=190,
        max_intermediate=1,
        tail_states=2,
        lenient_diagonals=True,
        charge_ms=700,
        charge_release_ms=220,
        dp_double_tap=False,
        dp_skip_down=False,
        negative_edge=True,
        mash_count=5,
        rotation_window_ms=500,
        rotation_slack=2,
    ),
    notes=(
        "Neo Geo four-button panel: A and B are the light punch and kick, C and D the heavy pair.",
        "SNK buffering is generous, so a quarter circle done as down, forward still comes out.",
        "No dragon punch shortcut: f,d,df means f,d,df, and holding down then tapping forward gives nothing.",
        "Charge moves want a little less than KoF '98 asks for.",
        "The guide is written in numpad notation, so the move list here is the translation of it.",
    ),
    reference="references/kof2001.txt",
    buttons=NEO_GEO,
)

SSVSP = GameSpec(
    key="ssvsp",
    name="Samurai Shodown V Special",
    short_name="SSV Special",
    ruleset=Ruleset(
        # A slower, more deliberate game than the KoF pair on the same panel:
        # you commit to a swing, and the motions are correspondingly plainer.
        # Windows sit near KoF '98's, with SNK's usual generous buffering.
        motion_window_ms=320,
        activation_window_ms=170,
        step_gap_ms=180,
        max_intermediate=1,
        tail_states=2,
        lenient_diagonals=True,
        charge_ms=900,
        charge_release_ms=220,
        dp_double_tap=False,
        dp_skip_down=False,
        negative_edge=False,
        mash_count=5,
        rotation_window_ms=500,
        rotation_slack=2,
    ),
    notes=(
        "Neo Geo panel, but not a Neo Geo brawler: A and B are the weak and medium slash,",
        "A+B the strong one, C kicks and D is the dodge button.",
        "SNK buffering is generous, so a quarter circle done as down, forward still comes out.",
        "No dragon punch shortcut: f,d,df means f,d,df.",
        "The supers need a full Rage gauge, which the trainer does not model - only the input.",
    ),
    reference="references/ssvsp.txt",
    buttons=NEO_GEO,
)

USFIV = GameSpec(
    key="usfiv",
    name="Ultra Street Fighter IV",
    short_name="USFIV",
    ruleset=Ruleset(
        # The most modern engine in the set: a deep special-move buffer,
        # forgiving charge partitioning and junk-tolerant motions, sitting
        # between Alpha 3 and 3rd Strike and leaning toward 3rd Strike for
        # leniency. SF4 is the shortcut game: it takes both of 3rd Strike's
        # dragon punch shortcuts, the diagonal (f,df on its own) and the
        # double-tap, which together are why players eat a DP walking up to
        # throw.
        motion_window_ms=340,
        activation_window_ms=200,
        step_gap_ms=200,
        max_intermediate=2,
        tail_states=3,
        lenient_diagonals=True,
        charge_ms=900,
        charge_release_ms=230,
        dp_double_tap=True,
        dp_skip_down=True,
        negative_edge=True,
        mash_count=5,
        rotation_window_ms=550,
        rotation_slack=3,
    ),
    notes=(
        "The shortcut game: f,df on its own gives a dragon punch, which is why you eat one walking up to throw.",
        "Hold down and double tap forward and you get a dragon punch too, as in 3rd Strike.",
        "Diagonals can be skipped, so d,f still reads as a quarter circle.",
        "Charge partitioning is forgiving and the special buffer is wide.",
        "Negative edge exists, so releasing a button can complete a special.",
    ),
    reference="references/usfiv.txt",
)

INPUT_DISPLAY = GameSpec(
    key="display",
    name="Input display",
    short_name="Inputs",
    # Nothing is recognised here, so the rules never come into it.
    ruleset=Ruleset(),
    notes=(
        "No moves and no rules: whatever you press is drawn as you press it.",
        "Pick the panel you want laid out; the keys come from your layout.",
    ),
    reference="",
)
"""A game only in so far as it is picked like one: it has no roster, and its
characters are the button sets. See :mod:`motioninput_tui.games.loader`."""

DISPLAY_GAME = INPUT_DISPLAY.key

# Menu order: the input display first, then by series (alphabetically), then in
# each series' own numeric / chronological order.
GAME_SPECS: dict[str, GameSpec] = {
    spec.key: spec for spec in (INPUT_DISPLAY, KOF98, KOF2001, SSVSP, HSF2, SFA3, SFIII3, USFIV)
}
DEFAULT_GAME = SFIII3.key


def get_spec(key: str) -> GameSpec:
    """Look up a game spec by key."""
    try:
        return GAME_SPECS[key]
    except KeyError:
        known = ", ".join(GAME_SPECS)
        message = f"Unknown game {key!r}. Known games: {known}"
        raise KeyError(message) from None
