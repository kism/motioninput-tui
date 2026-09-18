"""Per-game metadata and input rules.

The headline difference between these games is the dragon punch. Third Strike
will give you one for holding down and double tapping forward; Super Turbo and
Alpha 3 want a real f,d,df and will hand you a fireball if they do not get it.
"""

from dataclasses import dataclass

from motioninput_tui.controls.buttons import NEO_GEO, SNES_FIGHTER, STREET_FIGHTER, ButtonSet
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
        "The strictest game here. Motions must be clean and diagonals cannot be skipped.",
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
        super_freeze_ms=833,  # ~50 frames at 60fps.
        rotation_window_ms=500,
        rotation_slack=2,
        # Mika's rope running and Bison's Head Press, reckoned like the rest.
        chain_window_ms=700,
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
    # Every figure here is read off the decompiled game rather than estimated.
    # `CMD_MAIN.c` is the command interpreter and `cmd_data.c` the tables it
    # walks: twelve header words then four-word steps, `{type, frames, free,
    # lever}`, ending in 28. Frames are converted at 60fps. See
    # `docs/sfiii3-from-the-decomp.md`.
    ruleset=Ruleset(
        # A quarter circle is three steps ten frames apart, so 20 frames end to
        # end. The game has no whole-motion limit of its own - only the per-step
        # budget below - so this is set to what that budget implies and never
        # binds on its own.
        motion_window_ms=333,
        # `reset`, the frames a finished command waits for its button. Twelve,
        # identically, in all 174 of the game's special and super tables.
        activation_window_ms=200,
        # `w_int` on a direction step: ten frames. The half circles and the seam
        # between a super's two quarter circles get fourteen, and a dragon
        # punch's forward-to-down only five; ten is the one that governs most
        # steps of most motions.
        step_gap_ms=167,
        # Half circles, and the seam between a super's two quarter circles,
        # get fourteen frames instead: 90 of the game's 445 motion steps.
        wide_step_gap_ms=233,
        # And a dragon punch's forward to down gets five - but timed from
        # letting forward go, not from pressing it, so holding it costs nothing.
        tight_step_gap_ms=83,
        max_intermediate=2,
        tail_states=3,
        # `check_0` compares the lever for equality, so a fireball really is
        # `d, df, f` and a hitbox skipping straight from down to forward gets
        # nothing. The leniency people remember is in the half circles instead.
        lenient_diagonals=False,
        # `f, (d|db|df), b` - three checkpoints, the diagonals never named.
        half_circle_three_points=True,
        # `qcf,qcf` is `d, df, f, d, df`; the button ends it.
        double_motion_drops_tail=True,
        charge_ms=700,  # `check_1` free1: 42 frames, the same for every charge move.
        # And it accumulates: `check_1` never restores the count on release, so
        # the charge only starts over after 42 frames of not holding, added up.
        charge_reset_ms=700,
        charge_release_ms=167,  # Ten frames to reach the release direction.
        # `check_26` matches the lever bits pressed *this frame*, so a forward
        # tapped while down is already held still reads as a fresh forward.
        # That is the whole mechanism behind the shortcut.
        dp_double_tap=True,
        # The step after it wants an exact down, so f,df alone is not a dragon
        # punch however the shortcut is entered.
        dp_skip_down=False,
        negative_edge=True,
        mash_count=5,  # `check_4` fires at five presses of one button.
        mash_window_ms=1650,  # It wipes its counters every 99 frames.
        # And they are three counters, one per button strength, so rolling
        # across the kicks never reaches five of anything.
        mash_same_button=True,
        # Held where it was. This is a follow-through's pace, which for a super
        # lives in per-move script data the decomp does not carry - `check_4`'s
        # own 9 to 15 frames govern a mash *special* keeping itself going, which
        # is not the same thing. Guessing one from the other would be worse than
        # leaving it.
        mash_tap_gap_ms=600,
        super_freeze_ms=833,  # Still an estimate: the freeze is per move, in script data the decomp does not carry.
        rotation_window_ms=533,  # `check_6` w_int: 32 frames, one turn.
        rotation_cardinal_gap_ms=233,  # Its free1: 14 frames without a cardinal wipes the set.
        # `check_special_attack` runs before `check_jump_ready` each frame and only while
        # grounded, so the up a circle needs is a jump the frame after it is read. The
        # tables say nothing about how long pre-jump lasts, so this is Hugo in the
        # game's training mode: a button six frames after the up-back is still a
        # Moonsault Press, nine frames on he has jumped. Seven, as seven and eight
        # are unmeasured.
        jump_grace_ms=117,
        rotation_slack=2,  # Unread while the rule above is in force.
        # The one figure in this ruleset that is NOT from the decompilation:
        # a link's window lives in the same per-move script data the freeze
        # does, which the decomp does not carry. Reckoned at the same 700ms
        # as the other games, and flagged in docs/sfiii3-from-the-decomp.md
        # so it is not mistaken for a measured one.
        chain_window_ms=700,
    ),
    notes=(
        "The lenient one. Hold down and double tap forward and you get a dragon punch.",
        "Half circles are read at three points, so b, any down, f is one - the diagonals never matter.",
        "Quarter circles are not lenient: d,f with no down-forward between them is nothing.",
        "A super's second quarter circle stops at down-forward, the button standing in for the last step.",
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
        # KoF's rekka strings: the next hit is buffered during the one before,
        # so the window is generous. Reckoned, like the rest of this ruleset.
        chain_window_ms=700,
    ),
    notes=(
        "Neo Geo four-button panel: A and B are the light punch and kick, C and D the heavy pair.",
        "SNK buffering is generous, so a quarter circle done as down, forward still comes out.",
        "No dragon punch shortcut: f,d,df means f,d,df, and holding down then tapping forward gives nothing.",
        "Negative edge exists, so releasing a button can complete a special.",
        "Charge moves want most of a second in the held direction.",
        "The rekka strings chain: land the first and the next one opens for a moment.",
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
        # KoF's rekka strings: the next hit is buffered during the one before,
        # so the window is generous. Reckoned, like the rest of this ruleset.
        chain_window_ms=700,
    ),
    notes=(
        "Neo Geo four-button panel: A and B are the light punch and kick, C and D the heavy pair.",
        "SNK buffering is generous, so a quarter circle done as down, forward still comes out.",
        "No dragon punch shortcut: f,d,df means f,d,df, and holding down then tapping forward gives nothing.",
        "Charge moves want a little less than KoF '98 asks for.",
        "The guide is written in numpad notation, so the move list here is the translation of it.",
        "The rekka strings chain: land the first and the next one opens for a moment.",
    ),
    reference="references/kof2001.txt",
    buttons=NEO_GEO,
)

LB2 = GameSpec(
    key="lastbld2",
    name="The Last Blade 2",
    short_name="Last Blade 2",
    ruleset=Ruleset(
        # A quicker, more combo-minded weapon game than the Samurai Shodown
        # pair, but the same house buffering: nothing here asks for tighter
        # windows than the rest of the Neo Geo set.
        motion_window_ms=320,
        activation_window_ms=160,
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
        # Its follow-ups are the same shape as KoF's and reckoned the same way.
        chain_window_ms=700,
    ),
    notes=(
        "Neo Geo panel, weapon game: A and B are the weak and strong slash, C kicks and D repels.",
        "SNK buffering is generous, so a quarter circle done as down, forward still comes out.",
        "No dragon punch shortcut: f,d,df means f,d,df.",
        "Only Washizuka and Lee Rekka charge; everyone else is motion-only.",
        "Many specials chain: land the first and the move written after it opens for a moment.",
        "The DMs and SDMs want a full meter and the right mode, neither of which the trainer models.",
    ),
    reference="references/lastbld2.txt",
    buttons=NEO_GEO,
)

SAILORMOONS = GameSpec(
    key="sailormoons",
    name="Bishoujo Senshi Sailor Moon S",
    short_name="Sailor Moon S",
    ruleset=Ruleset(
        # A 1994 licensed SNES fighter, and nothing about it argues for tighter
        # windows than the arcade games here: it is slower and its motions are
        # plain. These are interpolated from Alpha 3's.
        motion_window_ms=320,
        activation_window_ms=170,
        step_gap_ms=180,
        max_intermediate=1,
        tail_states=2,
        # Left off deliberately. The guide spelling every diagonal out is a
        # notation habit rather than evidence about the engine, and there is no
        # decompilation to check, so this stays at the default a game only
        # turns on with real figures behind it.
        lenient_diagonals=False,
        # The one figure here that is not reckoned: the guide's own key says to
        # hold the direction for at least two seconds, which is far longer than
        # anything else in the trainer asks for.
        charge_ms=2000,
        charge_release_ms=220,
        dp_double_tap=False,
        dp_skip_down=False,
        negative_edge=False,
        mash_count=5,
        rotation_window_ms=500,
        rotation_slack=2,
    ),
    notes=(
        "Four buttons: weak and strong punch, with the two kicks beneath them.",
        "Charges are the longest in the trainer - the guide asks for a full two seconds.",
        "No dragon punch shortcut: f,d,df means f,d,df.",
        "The guide covers the SuperS sequel too; this roster is what the S game has.",
        "It writes forward as T, for towards, so the move list here is the translation of it.",
        "Its longest desperation motions are not ones the trainer models, so they are struck through.",
    ),
    reference="references/sailormoons.txt",
    buttons=SNES_FIGHTER,
)

SSII = GameSpec(
    key="samsho2",
    name="Samurai Shodown II",
    short_name="SSII",
    ruleset=Ruleset(
        # The same series and pace as SSV Special below, and nothing about the
        # 1994 engine argues for tighter windows than its descendant: you
        # commit to a swing, the motions are plain, and SNK buffering is
        # generous. Kept identical rather than invented apart.
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
        # Genjuro's and Seiger's strings, reckoned as the rest of the SNK set.
        chain_window_ms=700,
    ),
    notes=(
        "Neo Geo panel, weapon game: A and B are the light and medium slash, C and D the two kicks.",
        "A pair of either gives the heavy version, so the guide's Slash and Kick mean that pair.",
        "SNK buffering is generous, so a quarter circle done as down, forward still comes out.",
        "No dragon punch shortcut: f,d,df means f,d,df.",
        "The POW moves need a full meter, which the trainer does not model - only the input.",
        "Genjuro's SanRenSatsu chains: land one and the next opens for a moment.",
    ),
    reference="references/samsho2.txt",
    buttons=NEO_GEO,
)

SSVSP = GameSpec(
    key="samsh5sp",
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
        (
            "Neo Geo panel, but not a Neo Geo brawler: A and B are the weak and medium slash, "
            "A+B the strong one, C kicks and D is the dodge button."
        ),
        "SNK buffering is generous, so a quarter circle done as down, forward still comes out.",
        "No dragon punch shortcut: f,d,df means f,d,df.",
        "The supers need a full Rage gauge, which the trainer does not model - only the input.",
    ),
    reference="references/samsh5sp.txt",
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
        super_freeze_ms=1000,  # ~60 frames at 60fps.
        rotation_window_ms=550,
        rotation_slack=2,
        # Dudley's Ducking and Adon's Jaguar Assault, reckoned like the rest.
        chain_window_ms=700,
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

MARTMAST = GameSpec(
    key="martmast",
    name="Martial Masters",
    short_name="Martial Masters",
    ruleset=Ruleset(
        # IGS's 2001 PGM board, not a Neo Geo or a Capcom one, and there is no
        # decompilation to read. Nothing is measured here, so every field that
        # loosens the game stays off: the guide writes each motion out in full
        # and never abbreviates one, which is an argument for nothing. The
        # windows sit where Alpha 3's do, the nearest game whose dialect this
        # guide shares.
        motion_window_ms=300,
        activation_window_ms=150,
        step_gap_ms=170,
        max_intermediate=1,
        tail_states=2,
        lenient_diagonals=False,
        # Inert: nobody in this roster charges or turns a circle.
        charge_ms=900,
        charge_release_ms=200,
        dp_double_tap=False,
        dp_skip_down=False,
        negative_edge=False,
        mash_count=5,
        rotation_window_ms=500,
        rotation_slack=2,
        # Long enough to roll a deliberate quarter circle out of the move
        # before, short enough that the string does not outlive the animation
        # it belongs to. Most of this roster is chains, so this is the field
        # that matters most here.
        chain_window_ms=700,
    ),
    notes=(
        "Four buttons: light and heavy punch, with the two kicks beneath them.",
        "No dragon punch shortcut: f,d,df means f,d,df.",
        "Nobody in this roster charges or turns a circle, so every special is a plain motion.",
        "The Shadow Moves cost a super stock, which the trainer does not model - only the input.",
        "Most of each move list is chains: land the move above and the next one opens for a moment.",
        "The trainer has no opponent, so it takes the parent coming out as the hit landing.",
    ),
    reference="references/martmast.txt",
    buttons=SNES_FIGHTER,
)

# Menu order: by series (alphabetically), then in each series' own numeric /
# chronological order.
GAME_SPECS: dict[str, GameSpec] = {
    spec.key: spec for spec in (KOF98, KOF2001, LB2, MARTMAST, SAILORMOONS, SSII, SSVSP, HSF2, SFA3, SFIII3, USFIV)
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
