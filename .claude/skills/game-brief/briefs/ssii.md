---
game: ssii
panel: neo-geo
closest_parser: kof98
predicted_trainable: 45
model: Claude Sonnet 5
---
# Samurai Shodown II — brief

A Neo Geo weapon-fighter (the guide itself spells it "Samurai Showdown 2") whose headline quirk for this engine is that its throws are written "b or f + button" — one line covers both facing directions — which collapses to "no direction" for the recogniser far more often than it produces a trainable move.

## Roster

- **17 characters**, no teams, listed in one flat `MOVELISTS` section in this order: Haohmaru, Ukyo Tachibana, Galford, Charlotte, Gen-An Shiranui, Cham Cham, Wan Fu, Jubei Yagyu, Nakoruru, Hanzo Hattori, Earthquake, Kyoshiro Senryo, Genjuro Kibagami, Neinhalt Seiger, Caffeine Nicotine, Mizuki, Kuroko.
- Nothing to skip. Unlike `kof98`'s alternate-style sections, there is no table of contents, no boss-only prose section, and no "EX"/style-character variants — Mizuki (the boss) and Kuroko (a secret character, per the `INTRODUCTION` block) each get one ordinary `+---+`-boxed movelist entry alongside everyone else, so the parser needs no team- or alt-version skip logic at all.
- **Name override candidate** (`datagen/names.py`, key `caffeine-nicotine`): the guide's own `INTRODUCTION` prose calls him "Nicotine Caffeine," but every movelist heading says "Caffeine Nicotine." The two disagree within the same document — worth checking against another source before deciding which order to display, rather than assuming the heading is right.
- **Heading shape**: a fixed decorative box, identical on every character —
  ```
  +---------------------+
         Haohmaru
  +---------------------+
  ```
  Top and bottom lines are the *same literal string* for all 17 characters (only the name line's padding differs), and no team suffix or subtitle line ever appears.

## Guide anatomy (for the parser)

- There is no need for `SECTION_START`/`SECTION_END` slicing like `sfa3.py`/`sfiii3.py` use. The `MOVELISTS` banner (an `o---o` box, ~line 93 of the supplied text) is immediately followed by two lines of prose and then the first `+---+` box (~line 102); the cleanest trigger is the character-heading regex itself, hsf2-style — start collecting on the first `+---+` box, stop at the bare line `CREDITS` near the end of the file. `kof98.py` already uses `SECTION_END = "CREDITS"` for the same literal marker.
- **Useful accident**: `common.DASHED` (`^[\s|+-]*[-]{10,}[\s|+-]*$`) already matches this guide's `+---------------------+` box, because its character class includes `+`. It does *not* match the `o----------------------o` boxes used one level down for category headings, because `o` isn't in that class — so the two box styles are already distinguishable for free, no new regex needed for the outer box.
- **Character heading**: `DASHED`, then a name-only line (`^\s*([A-Za-z][A-Za-z'.\- ]{1,30}?)\s*$`), then `DASHED` again. No variants to handle.
- **Per-character blocks**: each has a `THROWS` box and a `SPECIAL MOVES` box, in the same `o----------------------o` / bare-word / `o----------------------o` shape `kof98.py`'s docstring shows for its own `SPECIAL MOVES` heading — reuse that dict-of-headings-to-`Category` idea (`_HEADINGS` in `kof98.py`) rather than hsf2's terse/verbose split; there is only one list per category here, not a terse-and-verbose pair.
- **Move lines** are `Name: command`, identical in shape to `kof98`'s `Name: command` (e.g. `Sake Kogeki: d, db, b + A`). Split on the last colon as `kof98.py` does — some names embed one (none observed yet in this cast, but it costs nothing to guard for).
- **Dialect**: directions already spelled as bare tokens (`d, df, f`, `d, db, b`, `f, d, df`, …), never `qcf`/`qcb` shorthand — same as `kof98`'s dialect. No `Charge` keyword and no `x2`/`720`/`360` notation appear anywhere in this cast (checked the whole guide): **no charge characters, no rotation motions** in Samurai Shodown II.
- **Line-level quirks**:
  - Air markers are inconsistent: `Hiken Tsubame Gaeshi: in air, db, d, df, f + Slash` puts "in air" as a *prefix* (which `normalise._AIR_PREFIX` already catches), but `Shinjou Rasen Kyaku: db, d, df, f + Kick in air` and `Fat Bound: d + Slash rapidly in air` put it as a *suffix*, which `_detect_air` (prefix-only) misses. The ss2 parser should move a trailing `in air` to the front before calling `parse_command`.
  - Condition prefixes largely match existing `_UNSUPPORTED` words (`when attacked`, `while attacked`, `during standoff` all already match `attacked`/`during`), but **`when damaged`** (`Gen-An Dappi: when damaged, BCD`) is not covered — "damaged" isn't in the list, so this reversal move silently parses as a plain 3-button press. Recommend adding `damaged` to `normalise._UNSUPPORTED` the way `kof98` added `from`. `at the peak of jump` (Kyoshiro's `Chikemuri Kuruwa`) has the same problem and no single keyword fix; flag it as a known gap rather than special-casing one move.
  - `unarmed,` prefixes (`Tsukami Nage: unarmed, b or f + B, D, AB, or CD`) are inert noise today — they don't match any button/direction token so they're silently dropped, which is harmless but means the trainer will teach the disarmed-only variant of a throw as if it always worked.

## Notation & engine fit

- **Buttons**: `A` = Light Slash, `B` = Medium Slash, `C` = Light Kick, `D` = Medium Kick, `AB` = Hard Slash, `CD` = Hard Kick — plus cross-family chords (`BC`, `ABC`, `BCD`) on a handful of moves. Panel is `NEO_GEO` (`neo-geo`).
- **A translation layer is mandatory, and `neogeo.py` doesn't cover this vocabulary as-is.** `kof98`'s dialect only ever writes `P`/`K`/`A`/`B`/`C`/`D`; this guide also writes the words `Slash` and `Kick` for "any button in that family," and multi-letter chords that cross families. A new ss2-specific table is needed, analogous in *shape* to `neogeo.to_shorthand`/`to_neo_panel` (translate to SF letters for `parse_command`, then remap the resulting `ButtonRequirement` back onto A/B/C/D), but with its own mapping: `A→LP`, `B→MP`, `C→LK`, `D→MK` (there is no third slash or kick, so `PUNCHES`/`KICKS`' three-member family doesn't apply directly — `Slash` should translate to an explicit `lp/mp` alternation, not the generic `p` token, or it will over-claim `HP` as a valid button), `AB→lp+mp`, `CD→lk+mk`, `BC→mp+lk`, `BCD→mp+lk+mk`, `ABC→lp+mp+lk`.
- **Token collision**: `b`/`d` direction tokens vs `B`/`D` button letters. Resolved the same way `kof98` resolves it — the guide is case-consistent (directions lower-case, buttons upper-case), so a case-sensitive translation regex is enough.
- **Throw button-lists need an explicit guard, not just a translation.** Most throws read `b or f + B, D, AB, or CD` (one `or`, several commas). `normalise._parse_buttons` only understands a clean two-way `X or Y`; fed this it splits on the single `/` into `"B, D, AB,"` and `"CD"`, and — since the two chunks aren't both length-1 — takes the *first* chunk whole, producing a fabricated `ButtonRequirement({MP, MK, LP}, count=3)` ("press all three at once"), not the intended "any one of four." The ss2 parser must detect >2-way comma lists in the button clause and route them to a skip (`unmodelled`-style), the same way `kof98.py` keeps unrecognised commands in the list, struck through, rather than mis-parsing them.
- **Direction-agnostic throws are the real headline quirk here.** Once that guard is in place, single-button throws (`Saishin Kiba: b or f + B`) correctly fail as "no directional or multi-button requirement" — the same bucket `kof98`'s command throws land in. But *two-button, non-alternating* throws such as `Satsu Renha: b or f + AB` resolve with no direction tokens and `buttons.count == 2`, which `_resolve_directions` turns into `MotionKind.ANY`, and `common.categorise` correctly reads as a `Category.THROW` — a genuinely trainable, direction-free throw. About a dozen of the 63 throw entries take this shape (mostly Wan Fu and Nakoruru, who favour bare `AB`/`CD` over the `X or Y` phrasing).
- **Motions not in `_MOTION_TABLE`/`_CHARGE_TABLE`** (skipped once the button side is fixed):
  - `f, b, db, d, df, f` (+ button) — a "mirror"/copy-projectile motion shared by ~8 moves across the cast (Galford's `Shadow Copy`, Earthquake's `Fat Copy`, Hanzo's `Ninpo Kage Bunshin`, Nakoruru's `Irusuka Yatoro Lise`, Wan Fu's `Shin Kikou Dai Bakuten`, Cham Cham's `Metamolie Animal Attack`, Caffeine's `Niou Furei Satsu`, Earthquake's `Earth Gaddemu`). Distinguishable from the table's own `HCB_F` (`f, df, d, db, b, f`) only by the position of the extra `b`. **Since added** as `MotionKind.F_HCF`: it turned out to be the standard SNK roll across four games rather than an SSII quirk, which is what made it worth a motion kind. 12 moves here now parse on it.
  - `Nuigurumi` — every character but Mizuki has one, and it's a different long, idiosyncratic sequence per character (e.g. `f, df, d, db, b, f, b + B` for Haohmaru, `db, d, df, f, d, df + D` for Kuroko). ~16 moves, none reused enough to be worth a table entry, unlike `kof98`'s compound supers.
  - A long tail of one-off 3-4 token shapes that just miss an existing entry — `f, db, d, df` (Haohmaru's `Ougi Kogetsu Zan`), `db, d, df` (Charlotte's `Power Gradation`, Gen-An's `Gen-An Utsusemi Dappi`), `db, d, df, f` (Ukyo's `Hiken Tsubame Gaeshi`, one token short of `TIGER_KNEE`) — roughly 15-20 moves total, one or two apiece.
  - Two 7-9 token "grand super" motions (Haohmaru's `Tenha Fuujin Zan`, Galford's `Backstab`) that are each unique to one move.
- **Predicted trainable: ~45%.** This is a hand-sample over about a third of the roster (5 of 17 characters' specials, all 63 throws), extrapolated — treat it as a estimate to be confirmed with `datagen --show-skipped` once the parser exists, not a measured figure. The two big losses: throws (only ~12 of 63 survive, because the `b or f` ambiguous-direction pattern dominates), and the idiosyncratic long-motion tail above (`Nuigurumi` plus the copy moves account for most of the rest of the loss).

## Ruleset rationale

No frame data for Samurai Shodown II specifically is something I'm confident of, so the numbers below are interpolated from `SSVSP` (the only other title on this panel with a similarly deliberate, non-combo-heavy feel) rather than measured — flag them for a real player's sanity check before shipping.

- Sits closest to `SFA3`/`KOF98` territory on the strict–lenient spectrum, not `SFIII3`: it has none of 3rd Strike's shortcut culture (no charge, no compound supers, no dragon-punch leniency), but it does need SNK's usual generous quarter-circle buffering.
- `dp_double_tap = False`, `dp_skip_down = False` — no evidence of an SF3-style shortcut in this cast; DP-shaped moves (`Ougi Resshin Zan: f, d, df + Kick`) want the real motion.
- `lenient_diagonals = True` — SNK buffering, consistent with every other Neo Geo title in this codebase.
- `charge_ms` / `charge_release_ms` / `rotation_window_ms` / `rotation_slack` — left at `Ruleset` defaults; **no charge or rotation motion appears anywhere in this guide**, so these fields are inert for this roster.
- `negative_edge = False` — following `SSVSP`'s precedent (same franchise); I have no specific evidence either way for this earlier entry.
- `motion_window_ms=320`, `activation_window_ms=170`, `step_gap_ms=180`, `max_intermediate=1`, `tail_states=2` — mirrored from `SSVSP` on genre proximity, not confirmed frame data.
- `mash_count=5`, `mash_window_ms=600` — several genuine mash moves exist (`Splash Fount: Slash rapidly`, `Hassou Happa`, `Fat Chainsaw`, `Kuroko Gekira: C rapidly`), matching the SNK default elsewhere in this codebase.
- **Charge characters: none.**
- **Headline quirk**: this is the plainest ruleset of the set — no charge partitioning, no rotations, no compound motions to teach. What it does uniquely surface is the direction-agnostic two-button throw (`b or f + AB`), which the engine happens to model as a bare `ANY`/`THROW` motion with no direction requirement at all.

```python
Ruleset(
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
)
```

## Test seeds

The harness lays `NEO_GEO` onto `HITBOX` exactly as it does for `kof98`; use the `NEO_A`/`NEO_B`/`NEO_C`/`NEO_D` aliases already defined in `harness.py` rather than the `HP`/`MK` names, since this game's `D` is a kick, not `SSVSP`'s dodge button — the comment in `harness.py` about Samurai Shodown's button names describes `SSVSP`, not this game.

- **haohmaru**: `QUARTER_CIRCLE_FORWARD_HP` presses `NEO_C` (key `o`, Light Kick here) after `d,df,f` → should give `Ougi Senpu Retsu Zan` (his `d, df, f + Slash`... actually that needs a Slash button, so use `NEO_A`/`NEO_B` for that one; a `d, df, f` + `NEO_C` script should instead miss, since his only kick-button special is the DP-shaped `Ougi Resshin Zan`). `DOWN_DOUBLE_TAP_FORWARD_HP` → `[]`, no shortcut, matching `hsf2`/`sfa3`/`kof98`.
- **wan-fu**: a custom script pressing `NEO_A` and `NEO_B` together with no direction held → `Satsu Renha`. The same script in any Street Fighter game in this trainer produces nothing (a two-button press needs *some* direction context or reads as a taunt); here it is a listed, trainable throw — the clearest demonstration of this game's direction-agnostic throw.
- **galford**: a clean `f, df, d, db, b` + button script → `Rear Replica Attack` (a plain `HCB`, once its `BCD` chord translates); the same motion with a trailing `f` added → `Mega Strike Heads` (`HCB_F`, already in `_MOTION_TABLE`), showing the parser correctly separates the two lengths.
- **charlotte** (or **jubei-yagyu**): repeated taps of `NEO_A`/`NEO_B` (`Slash`) with no direction → `Splash Fount` (`Hassou Happa` for Jubei) — a regression check that the `Slash`-word mash path actually resolves once translated, since `kof98`/`kof2001` never needed to handle that word.
