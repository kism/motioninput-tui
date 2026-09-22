---
game: sailormoons
panel: snes-4button
closest_parser: kof98
predicted_trainable: 67
model: Claude Sonnet 5
---
# Sailor Moon S & SuperS Fighting Games (SNES) — brief

A ten-character SNES 2D fighter whose FAQ writes directions as bare letters (`U D B T` plus `DB DT UB UT`) instead of any dialect the engine already understands, and whose own legend states an explicit charge time — "Hold position for at least two seconds" — nearly double every other game's charge estimate.

## Roster

- **10 characters**, one section each, no team grouping: Sailor Moon/Super Sailor Moon, Sailor Mercury, Sailor Mars, Sailor Jupiter, Sailor Venus, Sailor Chibi Moon/Super Sailor Chibi Moon, Sailor Uranus, Sailor Neptune, Sailor Saturn (SuperS Version ONLY), Sailor Pluto.
- **Skip** the `Universal Moves` section (~line 18–30, `Reverse Dash`/`Throw Recovery`) — it sits before any character heading and has no character to attach to. Skip the `Key` block (~line 7–15) and everything from the `****` rule (~line 250) onward (version history, credits) — no move content there.
- This guide is a "quick reference" for **two separate games** (S and SuperS) folded into one roster: `(S Only)` and `(SS Only)` tags mark version-exclusive moves on an otherwise shared character. The trainer has no concept of version exclusivity, so both tags' moves end up in one character's move list regardless — worth a deliberate decision, not something this brief resolves, since it means e.g. Sailor Moon gets both `Moon Spiral Heart Attack` (S) and `Moon Gorgeous Meditation` (SS) side by side.
- **Name overrides** (`datagen/names.py`, keyed by what `character_key()` produces from the raw heading): the two `/`-joined headings need one each, since `character_key("Sailor Moon/Super Sailor Moon")` produces `sailor-moon-super-sailor-moon`:
  - `sailor-moon-super-sailor-moon` → `Sailor Moon`
  - `sailor-chibi-moon-super-sailor-chibi-moon` → `Sailor Chibi Moon`
  Recommend the parser itself strip a trailing `(...)` from the heading before keying, so `Sailor Saturn (SuperS Version ONLY)` becomes `name="Sailor Saturn"`/key `sailor-saturn` without needing an override.
- **Heading shape**: a `Sailor `-prefixed name line immediately followed by a line of ten-or-more hyphens (`DASHED` from `common.py` matches it directly). Two blank lines usually precede it, one follows. The dashed line's length tracks the name's length (setext-style), which is what tells a character heading apart from a `====`-underlined section heading like `Individual Special Moves` (~line 34–35) or `Key` (~line 7–8) — those use equals signs, never hyphens, so requiring the underline to be `DASHED` (not `====`) already disambiguates them.

## Guide anatomy (for the parser)

- **Move-list section**: start at `Individual Special Moves` (~line 34; there is no table of contents in this guide, so no second-occurrence disambiguation is needed, unlike `sfa3`/`sfiii3`/`kof98`). End at the `****...****` rule before `Version History` (~line 250).
- **Character heading**: roughly `^Sailor\s[A-Za-z /()']+$` with the next line matching `DASHED`. No sandwiching dashed line above (unlike `sfiii3`/`kof98`'s banner style) — structurally closer to `hsf2`'s "header, then check the next line" approach, just with a different header regex and no `- Name -` decoration.
- **One block per character**, no terse/verbose split. Collection runs from the heading to the next heading (or end of section), skipping paragraphs that begin `NOTE` (~lines 63, 84, e.g. "Mercury can wall jump…") — these are prose asides with their own colon (`NOTE: Sailor Moon (S) and…`) that would otherwise misparse as a move named `NOTE`.
- **Move lines are `Name: command`, split on the *last* colon**, exactly `kof98`'s pattern — needed because qualifiers add their own colons: `(S Only): Moon Spiral Heart Attack: D DB B + Strong Punch or Punch` has two colons before the command; `rpartition(":")` still isolates the command correctly. Strip the `(S Only):`/`(SS Only):` prefix from the name afterward (a `kof98`-style `_ASIDE`-equivalent regex). `Desperation:`-prefixed names (one per character, e.g. `Desperation: Ginguishou (aka Ginzuishou): D DT T DT D DB B + Strong Kick.`) are that character's super — use the literal `Desperation:` prefix to force `category=Category.SUPER`, since there's no heading-group signal the way `kof98` has `SUPER MOVES`.
- **Continuation lines are the real anatomy difference from all four existing parsers.** Move descriptions wrap across 2–3 lines at ~78 columns and are delimited by blank lines, not fixed-width columns — e.g. `Twinkle Yell`'s entry (~line 170–171) splits its command across a line break, and several parentheticals (Mars Snake Flare, Jupiter Double Axle, Dead Scream) run 3+ lines. None of `hsf2`/`sfa3`/`sfiii3`/`kof98` need this: they all assume one move per line. This guide needs a **paragraph-joining pass first** — group lines into blank-line-delimited blocks, join each block with spaces, *then* run the `Name: command` split on the joined text.
- **Dialect**: bare-letter directions (`U D B T`, diagonals `DB DT UB UT`), `Charge X then Y` for charge moves, and `Strong Punch or Punch` / `Strong Kick or Kick` for "either strength" button requirements. None of this is any existing dialect; closest in *move-line shape* is `kof98`'s colon-split `Name: command`, so start there.

## Notation & engine fit

- **Buttons**: `A B X Y` on the SNES pad, meaning Weak Punch, Strong Punch, Weak Kick, Strong Kick (guide's own Key, ~line 10–11) — a 4-button weak/strong panel with **no medium**, unlike Street Fighter's three-per-family or the Neo Geo's four generic letters. No existing `ButtonSet` fits: `STREET_FIGHTER` has a medium the game doesn't; `NEO_GEO`/`TEKKEN`/`EIGHT_BUTTON` don't carry punch/kick identity at all. This needs a **new `ButtonSet`** in `buttons.py` — two rows, `(LP, HP)` over `(LK, HK)`, `MP`/`MK` simply never used. Proposed key `snes-4button`.
- **The panel still needs the `kof98`-style remap.** `normalise` only emits the Street Fighter six, and `"Strong Punch or Punch"` means "any Punch" — but this game's Punch family is only `{LP, HP}`, not the engine's default `PUNCHES = {LP, MP, HP}`. Translate to SF notation for `parse_command` (`Weak Punch`→`LP`, `Strong Punch`→`HP`, bare `Punch`→`p`), then remap the resulting `ButtonRequirement` down onto `{LP, HP}` before it reaches the panel — same shape as `datagen/parsers/kof98.py`'s `_neo_buttons`, just narrowing a 3-member family to 2 instead of relabelling it onto `A`/`C`.
- **Do not rely on `normalise`'s generic `"or"` → `"/"` handling for `"Strong Punch or Punch"`.** Passing `"hp or p"` through `_strip_noise` gives `"hp / p"`, and `_parse_buttons`'s alternatives logic only recognises the named `hp` (`"p"` isn't a specific `Button`), collapsing the whole phrase to `HP` alone — silently losing the "either strength" meaning. This idiom needs its own regex substitution (`"Strong (Punch|Kick) or (Punch|Kick)"` → `P`/`K`) before the command reaches `parse_command`, done once as a `sailormoons`-specific preprocessing step.
- **Direction letters need their own table, not `_WORD_DIRECTIONS`.** The guide's `B`/`DB`/`UB` happen to already equal the engine's own `b`/`db`/`ub` tokens, but `T`(owards)→`f`, `D`→`d`... wait `D`→`d` matches, `U`→`u` matches, and critically `DT`(down-towards)→`df` and `UT`(up-towards)→`uf` do **not** match letter-for-letter. Build an explicit `{"U":"u","D":"d","B":"b","T":"f","DB":"db","DT":"df","UB":"ub","UT":"uf"}` map and translate before calling `parse_command`.
- **`Charge X then Y` collides with `normalise._UNSUPPORTED`.** That regex bans the bare word `then` (meant to catch follow-up phrasing), and *every* charge move in this guide is written `Charge B then T` — so as written, every charge special (`Sonic Scream`, `Shabon Spray`, `Supreme Thunder Dragon`, `Venus Wink Sword`, `Submarine Reflection`, `Stork Sweep`) gets rejected as "conditional or follow-up move" before it ever reaches direction parsing. Rewrite `Charge X then Y` to a comma form (`Charge x,y`) in the pre-translation step, ahead of the `_UNSUPPORTED` check.
- **Motions not in `_MOTION_TABLE`/`_CHARGE_TABLE`** (after the above fixes, still skipped) — roughly one per character, mostly the Desperation supers and the close-range throws:
  - `R + <button>` "close" throws use `R`, which the guide's own Key says is an Easy-mode shoulder-button shortcut, not a direction — it isn't in `_DIRECTION_TOKENS` at all, so these read as no-direction, single-button and get dropped as "no directional or multi-button requirement." ~8 moves (`Slap Throw`, `Coconut Crusher`, `Frankensteiner`, `Reverse Leg Toss`, `Shoulder Toss` ×2, `Backflip`, `Head Pummel`, `Gut Knees`) — the same command-throw gap flagged in the `kof98` brief.
  - Fully spelled-out 360s: `Giant Swing` (`T DT D DB B UB U UT`, 8 tokens) and `Destructive Carnival` (`T DT D DB B DB D DT T`, 9 tokens) walk every compass point instead of writing "360," so `_parse_rotation`'s literal `"360"`/`"720"` string check never fires and the token tuples aren't `_MOTION_TABLE` keys either. 2 moves.
  - Assorted compound tuples not in the table: `Diving Gaia Crash` (`f,df,d,db,b,ub,u`), `Venus Wink Flare`, `Mars Snake Flare`, `Death Drive Break` (all 6–7 token compounds ending in a direction the table doesn't cover), `Mars Flame Sniper` (`f,b`, 2 tokens, no charge keyword), `Dragon Rise` (`f,d,df,f,d,df`), `Moon Gorgeous Meditation` (`d,db,b,f`), `Luna-P Attack` (`df,d,db,b`). ~8 moves.
  - Two entries look like guide typos rather than real inputs: `Jupiter Oak Evolution` (`D DT T A`) and `Pink Sugar Heart Attack` (`Charge A then T`) both use `A`, which the Key defines only as the Weak Punch *button*, never a direction; `Twinkle Yell` (`A DA D DT T D`) adds an undefined `DA` token too. `_direction_tokens` silently drops unrecognised chunks, so `Jupiter Oak Evolution` parses as a plain `qcf` (losing whatever the `A` was meant to add) while the other two fail outright. Flagged rather than "fixed," since it's not clear what the source intended.
- **Trainable ≈ 67%** (about 41 of 61 moves) once the `then`-strip and `Strong X or X` fixes are in place; without them the charge moves alone (6 more drops) would put it closer to 57%. What's left is the list above — command throws, spelled-out rotations, and a handful of compound supers the table doesn't model — plus the two probable typos.

## Ruleset rationale

Sits with `HSF2`/`SFA3` on strictness — no dragon-punch shortcut is documented or implied, diagonals are always spelled out in full (`T D DT`, `T DT D`, never a 2-token skip), and there's no `SFIII3`-style three-point half circle leniency anywhere in the notation. The one hard number the guide gives is unusually generous: charge is "at least two seconds," against 700–950ms everywhere else in `rulesets.py`.

- `dp_double_tap = False`, `dp_skip_down = False` — no DP-shortcut notation anywhere in the guide; this isn't a Capcom-lineage engine.
- `lenient_diagonals = False` — every diagonal-containing motion is spelled out token by token; nothing suggests a `d,f` shortcut is accepted.
- `half_circle_three_points = False` — no evidence of `SFIII3`'s leniency; the guide's half circles (`Dead Scream`: `B DB D DT T`) are written with every step named.
- `charge_ms = 2000`, taken directly from the guide's Key ("Hold position for at least two seconds") rather than estimated — the outlier figure in the whole ruleset file.
- `charge_release_ms = 220` — no source figure; kept near `SFA3`'s as an honest guess.
- `negative_edge = False` — unmeasured; no mention in the guide, defaulted conservatively rather than assumed.
- Everything else (`motion_window_ms`, `activation_window_ms`, `step_gap_ms`, `mash_count`, `rotation_window_ms`, `rotation_slack`) interpolated from `SFA3`, since nothing in the guide argues for different figures.
- **Charge characters**: Sailor Moon (`Sonic Scream`, d,u), Mercury (`Shabon Spray`, b,f), Jupiter (`Supreme Thunder Dragon`, b,f), Venus (`Venus Wink Sword`, d,u), Chibi Moon (`Pink Sugar Heart Attack`, garbled but charge-intent), Neptune (`Submarine Reflection`, b,f), Pluto (`Stork Sweep`, b,f) — 7 of 10. Mars, Uranus and Saturn are motion-only.
- **Headline quirk**: the two-second charge, nearly double every other game's, is the one game-feel fact this guide states outright rather than leaves to estimate — a charge held for a normal `SFA3`-length ~900ms should give nothing here.

```python
Ruleset(
    motion_window_ms=300,
    activation_window_ms=150,
    step_gap_ms=170,
    max_intermediate=1,
    tail_states=2,
    lenient_diagonals=False,
    charge_ms=2000,
    charge_release_ms=220,
    dp_double_tap=False,
    dp_skip_down=False,
    negative_edge=False,
    mash_count=5,
    rotation_window_ms=500,
    rotation_slack=2,
)
```

## Test seeds

- **sailor-moon**: a custom ~2000ms `DOWN` hold, release, `UP` + `HP` within `charge_release_ms` → `Sonic Scream`. The same script cut to a normal `SFA3`-length ~900ms hold should give `[]` — the one script in this whole roster where the charge duration itself, not the motion shape, is what's under test. `QUARTER_CIRCLE_FORWARD_HP` → `Moon Tiara Action`.
- **mercury**: a custom `f,d,df + HP` script (Towards, Down, Down-Towards) → `Reverse Break Step`. `DOWN_DOUBLE_TAP_FORWARD_HP` should give `[]` here, same as `sfa3`/`hsf2` — no dragon-punch shortcut, unlike `sfiii3`/`usfiv`.
- **jupiter**: a custom ~2000ms `BACK` hold, release, `FORWARD` + `HP` → `Supreme Thunder Dragon`. A custom `f,df,d + HP` script (Towards, Down-Towards, Down) → `Jupiter Coconut Cyclone`.
- **pluto**: `HALF_CIRCLE_SKIPPING_DOWN_MK` (with `HP` substituted for `Dead Scream`'s punch requirement) should give `[]` — with `half_circle_three_points=False`, the SOCD path that never hits a real `d` shouldn't register. `HALF_CIRCLE_THROUGH_DOWN_MK` (`HP` substituted) → `Dead Scream`.
