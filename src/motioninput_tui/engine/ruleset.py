"""Per-game input interpretation rules.

This is where the games actually differ from each other. The motion matchers in
``motions.py`` are generic; a :class:`Ruleset` decides how forgiving they are.

A field whose default is zero or false is one that only a game with real figures
behind it turns on. Those defaults are not the truth about how games behave, only
what the trainer falls back to with nothing to check against; where a game's
figures *are* known, the per-game file says so and cites them. See
``games/rulesets.py`` and, for the one game read off a decompilation rather than
a guide, ``docs/sfiii3-from-the-decomp.md``.
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
        wide_step_gap_ms: The same, for the steps a game is more generous
            about. Third Strike allows fourteen frames rather than ten for a
            half circle, and for the seam between a doubled motion's two
            halves. Zero means the game makes no such distinction.
        tight_step_gap_ms: The same, for the steps it is stricter about, and
            measured from letting the previous direction go rather than from
            arriving at it. This is the dragon punch, in a game that waits for
            forward to be released before looking for the down. Zero means the
            game makes no such distinction.
        max_intermediate: How many junk direction changes may sit between two
            steps of a motion. 0 means the motion must be clean.
        tail_states: How many direction changes may follow the end of a motion
            before the button press. A dragon punch usually leaves a trailing
            forward and a neutral behind it, and the game still accepts it.
        lenient_diagonals: Whether diagonals may be skipped entirely, so that
            d,f reads as a quarter circle forward. Third Strike does not: its
            command tables spell a fireball out as three exact directions,
            ``d, df, f``, so a hitbox going straight from down to forward gets
            nothing there.
        half_circle_three_points: Whether a half circle is checked at three
            points only - the start, any down, and the end - rather than at all
            five, so that it reads as ``b, (d|db|df), f`` with the diagonals
            never named. Otherwise the down has to be hit, which a keyboard's
            neutral SOCD makes of adding forward to down-back.
        double_motion_drops_tail: Whether the second half of a doubled motion
            stops one step short, the button standing in for the direction that
            would have ended it - ``qcf,qcf`` read as ``d, df, f, d, df``, which
            is why a super can come out of a hitbox that never reaches the last
            forward.
        charge_ms: How long a charge direction must be held.
        charge_reset_ms: How much time off the charge direction the game will
            forgive before the charge so far is forgotten. Non-zero makes the
            hold cumulative rather than unbroken: a game that never gives back
            what it has counted lets partial charge survive a release. Zero
            demands one unbroken hold, which is how the games with nothing to
            check against are still matched.
        charge_release_ms: How long after releasing a charge the follow-up
            direction and button may arrive.
        dp_double_tap: The Third Strike behaviour. When true, holding down and
            double tapping forward gives a dragon punch. SF2 and Alpha 3
            require a genuine f,d,df.
        dp_skip_down: Whether f,df alone can register a dragon punch.
        negative_edge: Whether releasing a button can trigger a special move.
            Recorded for display; the terminal cannot see key releases reliably.
        mash_count: Presses needed within ``mash_window_ms`` to start a mash
            move.
        mash_window_ms: How long those presses may be spread over. This is the
            *start* of a mash move only; a follow-through's taps are paced by
            ``mash_tap_gap_ms``.
        mash_tap_gap_ms: The longest gap between two taps of a follow-through
            before it is given up. Zero means the same as ``mash_window_ms``,
            which is how the two were one number to begin with. They are not
            the same quantity: 3rd Strike counts presses over 99 frames to
            start a mash move, and a tail's pace lives in per-move script data
            a game's own data may not settle.
        mash_same_button: Whether the presses have to be of one button. A game
            that keeps a counter per button strength fires when any single one
            of them reaches ``mash_count``, so rolling LK, MK, HK, LK, MK is
            two, two and one, and no move. False counts every press of any
            button the move accepts, which is how the games with nothing to
            check against are still matched.
        super_freeze_ms: How long a super's activation cinematic runs before the
            game reads inputs again. A mash or tap follow-through cannot start
            until it passes: press during it and the game never sees it, which
            is why mashing early feels like the move dropped your taps. Applies
            to supers only - a special with a mashable tail (Sakura Otoshi,
            Dee Jay's Machinegun Upper) has no cinematic and is read at once.
            One figure per game is an estimate: the real freeze is a little
            different per super, and Sean's Shouryuu Cannon in Third Strike is
            longer than the number here. Zero means unmeasured, which is
            harmless for a game whose roster has no super with a tail.
        rotation_window_ms: Window for one turn of a 360 or 720.
        rotation_cardinal_gap_ms: How long the game will wait between two
            cardinals before forgetting the ones already collected. Non-zero
            selects the rule where a rotation is the four cardinals in any
            order, compared for equality so that no diagonal counts towards
            one, gathered inside ``rotation_window_ms``. ``rotation_slack`` is
            not read then. Zero keeps the travel model below, which is what the
            games with nothing to check against are still matched with.
        rotation_slack: How many of the eight directions a rotation may skip.
            Games are forgiving about *which* directions you hit - rolling
            through four keys travels six of the eight and counts - but not
            about letting go: a neutral anywhere in the circle restarts it, in
            every game. Two is as loose as this should get. At three, a half
            circle back that carries one notch past back is a whole revolution,
            which is a move the games do not give you.
        jump_grace_ms: How long a move that has to be done on the ground
            survives the lever reaching up. Up is a jump input - diagonals
            included - so from that moment the character is committed, and this
            is the jump's startup, the last of it that is still spent standing.
            Press the button after and the game is reading someone airborne and
            gives nothing at all until they land. It is what makes a leisurely
            roll around the gate a jump rather than a command throw, and why a
            360 is finished *with* the button rather than after it. Zero means
            the trainer has no figure for the game and lets every move stand on
            its own.
    """

    motion_window_ms: int = 300
    activation_window_ms: int = 150
    step_gap_ms: int = 180
    wide_step_gap_ms: int = 0
    tight_step_gap_ms: int = 0
    max_intermediate: int = 1
    tail_states: int = 2
    lenient_diagonals: bool = False
    half_circle_three_points: bool = False
    double_motion_drops_tail: bool = False
    charge_ms: int = 900
    charge_reset_ms: int = 0
    charge_release_ms: int = 200
    dp_double_tap: bool = False
    dp_skip_down: bool = False
    negative_edge: bool = False
    mash_count: int = 5
    mash_window_ms: int = 600
    mash_tap_gap_ms: int = 0
    mash_same_button: bool = False
    super_freeze_ms: int = 0
    rotation_window_ms: int = 500
    rotation_cardinal_gap_ms: int = 0
    rotation_slack: int = 2
    jump_grace_ms: int = 0
