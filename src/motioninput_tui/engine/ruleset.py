"""Per-game input interpretation rules.

This is where the games actually differ from each other. The motion matchers in
``motions.py`` are generic; a :class:`Ruleset` decides how forgiving they are.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Ruleset:
    """How strictly a game reads the input buffer.

    Attributes:
        motion_window_ms: How long a whole motion may take from first to last
            direction. Shorter is stricter.
        activation_window_ms: How long after finishing a motion the button may
            be pressed and still count.
        step_gap_ms: The longest pause allowed between two steps of a motion.
            This is what stops a direction left over from an earlier input
            acting as the start of a later one.
        max_intermediate: How many junk direction changes may sit between two
            steps of a motion. 0 means the motion must be clean.
        tail_states: How many direction changes may follow the end of a motion
            before the button press. A dragon punch usually leaves a trailing
            forward and a neutral behind it, and the game still accepts it.
        lenient_diagonals: Whether diagonals may be skipped entirely, so that
            d,f reads as a quarter circle forward.
        lenient_half_circles: Whether the down of a half circle may be db or df
            rather than straight down, so b,db,df,f counts as one. Adding
            forward while back is still held goes straight to df, so an
            ordinary hitbox half circle never touches down at all. Unlike the
            rest of this class it is the player's choice rather than the game's:
            :mod:`motioninput_tui.settings` folds it in on top of the game's
            own rules.
        charge_ms: How long a charge direction must be held.
        charge_release_ms: How long after releasing a charge the follow-up
            direction and button may arrive.
        dp_double_tap: The Third Strike behaviour. When true, holding down and
            double tapping forward gives a dragon punch. SF2 and Alpha 3
            require a genuine f,d,df.
        dp_skip_down: Whether f,df alone can register a dragon punch.
        negative_edge: Whether releasing a button can trigger a special move.
            Recorded for display; the terminal cannot see key releases reliably.
        mash_count: Presses needed within ``mash_window_ms`` for a mash move.
        mash_window_ms: Window for mash moves.
        rotation_window_ms: Window for 360 and 720 motions.
        rotation_slack: How many of the eight directions a rotation may skip.
            Games are famously forgiving here; a 360 done as f, d, b, u counts.
    """

    motion_window_ms: int = 300
    activation_window_ms: int = 150
    step_gap_ms: int = 180
    max_intermediate: int = 1
    tail_states: int = 2
    lenient_diagonals: bool = False
    lenient_half_circles: bool = True
    charge_ms: int = 900
    charge_release_ms: int = 200
    dp_double_tap: bool = False
    dp_skip_down: bool = False
    negative_edge: bool = False
    mash_count: int = 5
    mash_window_ms: int = 600
    rotation_window_ms: int = 500
    rotation_slack: int = 2


STRICT = Ruleset()
"""Sensible strict default, roughly Super Turbo."""
