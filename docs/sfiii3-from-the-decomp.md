# Third Strike, from the decompiled game

Almost every figure in `SFIII3`'s `Ruleset` is read out of the [3s-decomp][decomp]
project rather than estimated from play or from a guide. This page is how to
check them, and what the game turned out to do that the trainer had wrong.

Two are not from the decomp and are marked where they appear: `jump_grace_ms`,
which is pre-jump measured in the game's training mode, and `super_freeze_ms`, which is the activation
cinematic counted off in MAME (~50 frames) because it is an animation length
rather than an input rule and does not live in the command tables.

[decomp]: https://github.com/Vatuu/3s-decomp

## Where the input rules live

Two files under `src/anniversary/sf33rd/Source/Game/`:

* `CMD_MAIN.c` is the interpreter. `waza_check` runs once per frame per player,
  `sw_pick_up` samples the pad, and `cmd_move` walks all 56 of a character's
  command slots.
* `cmd_data.c` is the data it walks: one `const s16` array per command.

The lever is four bits, **facing-normalised** by `pl_lvr_set`, so a command is
written once and works on both sides:

| bit | 1 | 2 | 4 | 8 |
|---|---|---|---|---|
| | up | down | forward | back |

`sw_lever` is what is held now; `sw_now` is only what was *newly pressed this
frame*. That distinction turns out to be the whole dragon punch shortcut.

## The table format

Twelve header words, then four-word steps, then `28` to end:

```
reset, w_dead, w_dead2, waza_r[4], btix, exdt[4],   # 12-word header
type, frames, free, lever,                          # one step, repeated
28                                                  # terminator
```

`type` indexes `chk_move_jp`, **off by one** - type 1 is `check_0`, type 2 is
`check_1`, and type 0 is `check_init`, which is what "restart this command"
means. `lever` with `0x8000` set is compared for equality; without it, it is an
OR-mask; `frames` is that step's budget, decremented every frame.

Ryu's shoryuuken, `p2_cmd_28`:

```c
{ 12, 1, 0, 17,17,17,17, 1029, 0,1,2, 19,   // header: reset = 12
  27,  1, 0, -32764,                        // check_26, forward tapped and left
   1,  5, 0, -32766,                        // exact down, within 5 frames
   1, 10, 0, -32762,                        // exact down-forward, within 10
  28 }
```

`scripts/decode-3s-commands.py` prints all 20 characters' tables this way.

## The numbers

At 60fps. Every one of these is uniform across the roster unless noted.

| What | Frames | ms | Where |
|---|---|---|---|
| Gap between steps of a motion | 10 | 167 | `check_0` `w_int`, 335 of 445 steps |
| Gap in a half circle, and at a super's seam | 14 | 233 | 90 steps: 60 seams, 30 half circles |
| Dragon punch, forward to down | 5 | 83 | 18 tables, timed from the release |
| Button window after the motion completes | 12 | 200 | `reset`, all 174 tables |
| Charge hold, cumulative | 42 | 700 | `check_1` `free1`, every charge move |
| Charge forgotten after, cumulative | 42 | 700 | `check_1` `w_int` |
| Charge release to direction | 10 | 167 | the step after it |
| 360 | 32 | 533 | `check_6` `w_int` |
| 360, gap between cardinals | 14 | 233 | `check_6` `free1` |
| 360, up to button before the jump | 7 | 117 | pre-jump, **measured**, Hugo |
| Mash, presses needed, of one button | - | - | 5, `check_4` |
| Mash, window those presses fall in | 99 | 1650 | `check_4` `w_int` |
| Dash, gap between taps | 6 | 100 | `pc_cmd_00` |

The game has **no whole-motion time limit**. Only the per-step budget exists,
which is why `motion_window_ms` is set to what that budget implies and never
binds on its own.

Those three gaps are `step_gap_ms`, `wide_step_gap_ms` and `tight_step_gap_ms`,
carried to the step that the game actually times by `Pace` in `motions.py`. A
step's budget starts when the step *before* it landed, which is why the pace
lives on the later step of a pair. Games with no figures leave the two extra
gaps at zero and every step falls back to `step_gap_ms`.

The dragon punch's five frames come with a second half that matters as much as
the number. `check_26` does not advance until forward is no longer the lever's
exact direction, so the five frames run from the **release**, and holding
forward first costs nothing. Taking the number without the reference point
would have made the trainer far stricter than the game rather than more
accurate.

## What the trainer had wrong

**Quarter circles are strict.** A fireball is `d, df, f` compared for equality.
`lenient_diagonals` was `True` here on the belief that `d,f` reads as a quarter
circle; it does not, and a hitbox player who releases down before pressing
forward gets nothing. Third Strike is *stricter* than Super Turbo on this point,
not looser.

**Half circles are read at three points.** `f, (d|db|df), b` - the diagonals are
never named and the middle step is an OR-mask, so any down will do. Eleven
tables use this shape against four that spell all four directions out. It is
why a half circle that skips straight down counts here and nowhere else.

**A super's second quarter circle stops early.** `qcf,qcf` is `d, df, f, d, df`
- the button lands in place of the forward that would have ended it. Sixty of
the game's tables are that one shape, making it the most common motion in the
game.

**360s are about pace, not about letting go.** `check_6` collects the four
**exact cardinals** in any order - a diagonal counts towards nothing - and wipes
the set after 14 frames without the lever resting on one, or 32 frames for the
turn. A neutral is not special. So four separate taps of up, down, forward and
back *are* a 360, if they are quick enough. The trainer used to accumulate
travel around the ring and restart on a neutral; `_match_rotation_cardinals` now
implements the real rule, and the travel model stays only for the games there is
no decompilation to check.

One simplification, marked in the source: the game's 32-frame budget is a
free-running bucket rather than a window the player opens, so a turn quick
enough can still fail by straddling a boundary. The trainer has no frame clock
sharing the game's phase, and losing a good 360 to luck teaches nothing, so the
budget is the best window the player could have had. A held cardinal is re-set
every frame, so it is timed from the last moment it was held: walking forward
into a circle costs nothing.

**What actually makes a 360 hard is that up is a jump.** The command tables have
nothing to say here - the four rotation commands set `w_dead` to zero, so the
interpreter never cancels them - and the answer is one file over. `PLS00.c`'s
standing routine calls `check_special_attack` before `check_jump_ready` every
frame, and `check_special_attack` only looks at its table while
`xyz[1].disp.pos <= 0`, on the ground. `check_jump_ready` fires on the up bit
being *held*, diagonals included, so the moment a circle touches up-back on its
way round the gate the character is committed. The button then has the jump's
startup to land in; after that it is being read airborne and gives nothing.

Pre-jump keeps `check_special_attack` alive - `nm_16000`, the jump-ready
routine, calls it too - which is why a 360 comes out at all from standing. Its
length is the one figure here that is *not* read off the game: it lives in
per-character animation data the decomp does not carry, so `jump_grace_ms` is
measured instead, on Hugo in training mode: the button six frames after the
up-back is still a Moonsault Press, and nine frames on he has jumped. It is set
to seven, since seven and eight are unmeasured. An earlier guess of four frames
was well short of that. Before
this the trainer gave a leisurely roll round the gate a Moonsault Press every
time, which is the single biggest reason a 360 felt free here and rare in the
arcade.

**It is not a rule about circles.** `check_special_attack`'s ground test guards
every special and every super in the game, so the same thing happens to a half
circle back that overshoots to up-back: Hugo is in the air, and the Ultra Throw
the trainer used to award for it is not something the game would have given.
`_match_ground` in `motions.py` is that test, the mirror of `_match_air` and
sharing its `AIR_MEMORY_MS` - an up puts the character in the air for as long as
an air move counts, and for exactly that long a grounded one cannot.

Rotations are the exception, judged per turn by `_match_rotation_cardinals`
instead, since a circle cannot avoid an up and only the turn in progress can
fairly be held against it. The trainer has no airborne state to carry, so a 720
whose first revolution jumped away is taken on trust - the way to land one is
out of a jump or a move's recovery, where the up was never a jump to begin with.

**A mash is five presses of one button, not five presses.** `check_4` keeps
three counters, one per button strength, and fires when any single one reaches
five - so rolling LK, MK, HK, LK, MK is two, two and one, and no move. It counts
over 99 frames, which is a good deal slower than mashing, and wipes all three on
that cadence. Only one move in the roster is matched this way, Chun-Li's
Hyakuretsu Kyaku, and the trainer used to take the rolled kicks.

That is also what told `mash_window_ms` apart from the gap a *follow-through*
allows between taps, which the same field used to serve. They are different
quantities: 99 frames to start a mash move against a tail's own pace, which for
a super lives in per-move script data the decomp does not carry. `check_4`'s
other figures - 9 frames for a heavy button, 12 for a medium, 15 for a light -
govern a mash special keeping *itself* going, which is a third thing again and
is not modelled. `mash_tap_gap_ms` holds the seven moves with a tail exactly
where they were.

**A charge accumulates; it does not have to be unbroken.** `check_1` counts
`free1` down while the direction is held and, on release, assigns
`free2 = free1` - restoring nothing. Nothing reloads `free1` short of the
command resetting, which takes 42 frames of *not* holding, added up. So charge
for twenty frames, let go for forty, charge for twenty-two more, and it is
ready. Every charge move in the game uses this path, and the trainer used to
demand one unbroken hold, which made all thirteen of them harder here than in
the game.

**The dragon punch shortcut is real, and it is not a skipped down.** `check_26`
matches the lever bits pressed *this frame*, so a forward tapped while down is
already held still counts as a fresh forward. It then advances as soon as the
lever is no longer exactly forward, and the next step wants an exact down. So
holding down and double tapping forward works, and `f, df` on its own does not -
`dp_skip_down` is `False`.

## Still open

**Keeping a mash going.** Once `check_4` has fired, one more press of that
strength refreshes it, and the counters then wipe after only 9 frames for a
heavy button, 12 for a medium, 15 for a light. The trainer re-activates on each
further press instead, which is close enough in effect and would need per-move
state for one move.

**A pending command is killed by the lever sitting at exactly up.**
`dead_lvr_check` compares `w_dead` against the whole input word, and 92 of the
game's 177 special and super tables set it to 1 - up alone, no button. It is
there to stop a buffered special coming out of a jump. Not modelled: reaching
pure up between two steps of a motion means releasing the direction you came
from and pressing it again, which recreates that step anyway, and the trainer
has no notion of being airborne. The four rotation tables are not among the 92,
which is why a circle's own up is handled by the jump instead.

**Super freeze.** `comm_stop` takes its duration from per-move script data,
which the decomp does not carry - it lives in the disc's character files. It
confirms the trainer's model, though: `sa_stop_lvdir` snapshots the lever only
when the freeze ends, so inputs during it really are discarded.

**The roster.** The move lists are parsed from a GameFAQs guide, not from these
tables. Comparing them by motion shape and button gives 166 commands in the
decompilation against 161 in the roster, with ten of the twenty characters
matching exactly. Some of the difference is an artefact of matching that way -
an air Tatsumaki has its own table but one roster entry - but not all of it: Q,
Twelve and Gouki each disagree on three or four. The tables carry no move names,
so pairing them up is the work.

Comparing this way is worth doing for its own sake. It is what caught Elena's
Healing, which the guide writes as `qcf,qcf + P, then PP to cancel`: the parser
read the "then" as a follow-up condition and dropped the move, when the cancel
is only something the player may do afterwards. `p8_cmd_22` is an ordinary
`qcf,qcf` on punch, and it is now trainable.
