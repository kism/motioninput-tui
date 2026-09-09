---
game: usfiv
panel: street-fighter
closest_parser: sfiii3
predicted_trainable: 80
---
# Ultra Street Fighter IV — brief

Capcom's fourth-generation fighter, 44 characters on the standard six-button panel; its headline quirk is a heavily-buffered engine that will hand you a Shoryuken from just `f, df` yet refuses 3rd Strike's hold-down-double-tap-forward shortcut.

## Roster

- **44 characters**, listed alphabetically (the guide does not group by team). Under `3.  CHARACTER MOVELISTS`: Abel, Adon, Akuma, Balrog, Blanka, C.Viper, Cammy, Chun-Li, Cody, Dan Hibiki, Decapre, Dee Jay, Dhalsim, Dudley, E.Honda, El Fuerte, Elena, Evil Ryu, Fei Long, Gen, Gouken, Guile, Guy, Hakan, Hugo, Ibuki, Juri, Ken Masters, M. Bison, Makoto, Oni, Poison, Rolento, Rose, Rufus, Ryu, Sagat, Sakura Kasugano, Seth, T.Hawk, Vega, Yang, Yun, Zangief.
- **Skip**:
  - The `TABLE OF CONTENTS` (~line 118): it repeats ` 3.  CHARACTER MOVELISTS` followed by an indented `- Abel` … `- Zangief` list. Take the **second** occurrence of the marker (the `====`-bannered one, ~line 300).
  - Everything from ` 3.  SECRETS AND TRICKS` (~line 1760): `FIGHT AKUMA` / `FIGHT GOUKEN` / `FIGHT EVIL RYU` / `FIGHT ONI` / `EXTRA COSTUMES` are unlock-condition prose with no inputs. This is also the parse end marker.
  - Never reached if you stop there, but note for safety: ` 4.  GAMEPLAY NOTES`, ` 5.  MISCELLLANEOUS` (the `TRANSLATIONS` block, ~line 2010, is a `Japanese name␠␠English gloss` table that reads exactly like move lines), ` 7.  AUTHOR'S NOTE`.
  - **Edition Select** is mentioned in the `INTRODUCTION` (~line 175, "lets you play as different versions of most of the characters") but — unlike Hyper SF2 — the guide gives exactly one move list per character. There is no per-edition block to parse or skip.
- **`datagen/names.py` overrides** (keyed by the key `character_key()` makes from the ALL-CAPS heading):
  - `m-bison` → `M. Bison` — `finish_character` does `name.title()`, which yields `M.Bison` and drops the conventional space.
  - `dan-hibiki` → `Dan`, `ken-masters` → `Ken`, `sakura-kasugano` → `Sakura` — the guide headings carry surnames the in-game lists and the other Capcom games in this repo do not. See the parser note below: this is really a **key** problem (`ken-masters` ≠ the `ken` that `hsf2.py`/`sfa3.py` produce), and `names.py` only fixes the display string.
  - Everyone else title-cases cleanly (`E.HONDA` → `E.Honda`, `DEE JAY` → `Dee Jay`, `EL FUERTE` → `El Fuerte`, `C.VIPER` → `C.Viper`).
  - Also confirm the shared keys — `ryu`, `ken`, `chun-li`, `guile`, `blanka`, `dhalsim`, `zangief`, `sagat`, `vega`, `balrog`, `m-bison`, `e-honda`, `cammy`, `fei-long`, `dee-jay`, `t-hawk`, `akuma`, `dan` — resolve to the **same** display string here as in `hsf2`/`sfa3`/`sfiii3` if `names.py` is a flat key→name map.
- **Heading shape**: one leading space, ALL-CAPS name, between two ` ----…` rules (~73 dashes). Variant: right-padded name plus a parenthetical — `AKUMA … (GOUKI in JPN)`, `BALROG … (M.BISON in JPN)`, `M.BISON … (VEGA in JPN)`, `VEGA … (BALROG in JPN)`, `SETH … (Final Boss)`. The parenthetical is trivia: discard it (or stash as `title`), never let it into the key.

## Guide anatomy (for the parser)

- **Move-list section**: from the second ` 3.  CHARACTER MOVELISTS` (~line 300) to ` 3.  SECRETS AND TRICKS` (~line 1760). Note the guide's own numbering typo — the TOC calls these sections 3 and 4, the body headers both say 3. `sfiii3.py`'s `SECTION_END = "3.  SECRETS AND TRICKS"` matches as-is; `SECTION_START` must change from `2.` to `3.  CHARACTER MOVELISTS`.
- **Character heading**: `^ ?([A-Z][A-Z0-9.'\- ]{1,30}?)(?:\s+\([^)]*\))?\s*$`, sandwiched by `DASHED` above and below. `sfiii3.py`'s `_HEADER` only handles a `,`-suffixed subtitle and has no leading-space slack, so it misses every parenthetical heading (Akuma, both Bisons, Vega, Seth); borrow `sfa3.py`'s `(?:\s+\([^)]*\))?`.
- **Which block**: there is only one list per character. Parse from the heading to the first of: a `_STOP` line (`^\s*(Target Combos|Link Combos|Combos)\s*:` — the guide writes `Target Combos:` with entries following on indented continuation lines, none of which should be parsed) or the next heading.
- **Notation dialect**: identical to Alpha 3 / 3rd Strike shorthand — `qcf + P`, `hcf + K`, `f,d,df + P`, `b,d,db + K`, `Charge b,f + P`, `Charge d,u + K`, `qcf,qcf + PPP`, `Rotate 360 / 720 + P`. Spelled out in the ` FAQ NOTATION` block (~line 255): `qcf / hcf  -  Input (d,df,f) or (b,db,d,df)`, `Charge b,f / d,u  -  Hold … for two seconds`. **Closest parser: `sfiii3.py`** — it already has the flag-column regex (`EX`, and `I` / `II` here are the two Ultra Combos) and the two-rule header sandwich.
- **Line-level quirks**:
  - **Follow-up lines** `     - Second Mid                    - f + P`. `sfiii3.py` ends the whole character list on any `line.lstrip().startswith("- ")`, which would truncate nearly every character at their first chained special (Abel loses everything after `Change of Direction`). Change this to a plain `continue` — skip the line, do **not** end the list and do **not** feed it to `build_move` (they all carry `after` / bare `-` and are non-trainable anyway; counting them drags the denominator into the low 70s). Keep `_STOP` as the only list-ender. Prose notes (` - EX Cannon Strike can be done…`) are caught by the same `continue`.
  - **Parent lines** end `qcf + P, then...` / `f,d,df + K, then...` — `normalise._UNSUPPORTED` matches `then`, so they fall out as non-trainable (correct).
  - **Armor-break suffix** ` [AB]` trails many commands (`qcb + K [AB]`); harmless to `normalise` (not a button token) but strip it for a clean `notation` string.
  - Condition/air prefixes present and already handled by `normalise`: `In air,` / `(air)`, `While jumping u / uf,` (→ `while`, skipped), `When close,` / `Close,` (stripped), `Just before … hits,`, `During …` (skipped), `Jump against a wall, press f` (→ `against a wall`, skipped), `Hold and release PPP` / `Hold P, then release` (skipped), `when near a knife` / `When armed` (Cody, skipped).
  - **Surname headings**: `KEN MASTERS`, `DAN HIBIKI`, `SAKURA KASUGANO` produce keys `ken-masters` / `dan-hibiki` / `sakura-kasugano` that diverge from the `ken` / `dan` the other Capcom parsers emit. Either truncate these three headings to the first word in the parser, or accept the long keys and document the divergence.

## Notation & engine fit

- **Buttons**: the Street Fighter six (`LP MP HP` / `LK MK HK`), panel `STREET_FIGHTER`. No panel translation is needed — unlike `kof98.py` / the Neo Geo games, `normalise` already speaks this dialect natively, so nothing like `datagen/parsers/kof98.py`'s `_neo_buttons` remap applies here.
- **Token collisions**: none of consequence. Directions are lower-case tokens (`f,d,df`), buttons are `P`/`K`/`PP`/`PPP`/`LP…HK`; `normalise` lower-cases first and there is no `b`/`d` button letter on this panel to clash with the `b`/`d` directions.
- **Motions absent from `normalise._MOTION_TABLE` / `_CHARGE_TABLE`** (token sequence → cost):
  - `Charge b,df` → `(b,df)` — Balrog's Dash Ground Straight / Dash Ground Upper / Dash Swing Blow — **~3 moves**.
  - `Charge db,f` → `(db,f)` — Vega Scarlet Terror — **1**.
  - `Charge db,f,b,f` → `(db,f,b,f)` — Vega Splendid Claw (Ultra II) — **1**.
  - `d,d` — Hugo Leap Attack; `d,d,d` — Hakan Oil Combination Hold (Ultra II); `u,u` — Akuma Demon Armaggedon (Ultra II) — **~3**.
  - `Tap d,u` uncharged → `(d,u)` (only a charge-table key) — C.Viper / Ibuki High Jump — **2**.
  - `Jump forward, d + MK at apex` → `(f,d)` after the air words strip — the Tenma Kujin Kyaku dive kick shared by Akuma, Gouken, Evil Ryu, Oni, Seth — **~5**.
  - Total "unrecognised motion" skips: **~15 moves**.
  - Plus `_UNSUPPORTED` skips (`then` / `while` / `during` / `against a wall` / hold-and-release / knife / armed): **~45 moves**.
  - Plus no-direction-single-button lines (`Close, b / f + MP`, `HK,HK`, `Press HP when standing from afar`) → "no directional or multi-button requirement": **~12 moves**.
- **Mis-modelled but still counted trainable** (worth a test to catch, not a skip):
  - Raging Demon `LP,LP,f,LK,HP` / `LP,LP,b,LK,HP` → parsed as `MotionKind.ANY`, 3-button (categorised THROW). Akuma ×2, Evil Ryu, Oni — **4 moves** that "train" as a triple-button mash, not the real sequence.
  - `f,d,df / b,d,db + PPP / KKK` (Ashura Senkuu / Yoga Teleport / Bison Warp) → the parser keeps only the first alternative and reads `DP + PPP`. Roughly right for the forward teleport, wrong for the label — **~5 moves**.
- **Predicted trainable ≈ 80%**. The clean core is large (throws register as `HOLD` + two buttons; every fireball, dragon punch, `hcb`/`hcf`, charge `b,f` / `d,u` / `b,f,b,f`, `db,df,db,uf`, `qcf,qcf` / `qcb,qcb` / `hcb,hcb` super, and `Rotate 360`/`720` is in the tables). The ~20% loss is almost entirely **chained specials** (`, then...` parents plus their `- ` follow-ups across ~15 characters — Abel, El Fuerte, Gen, Decapre, Rolento, Cammy, Vega, the Hyakkishu shotos), the **command-throw-free but wall-jump / hold-release / stance** lines, and the handful of odd charge partitions above. This number is an estimate; the exact figure swings ~8 points on the `- `-line decision, so verify with `datagen --show-skipped` once the parser is written.

## Ruleset rationale

USFIV is the most modern engine in the set. It sits **between `SFA3` and `SFIII3`, leaning `SFIII3`** for leniency — a deep (~7–10 frame) special-move buffer, forgiving charge partitioning, junk-tolerant motions, and diagonal leniency on quarter circles — **but** it does *not* use 3rd Strike's "hold down, double-tap forward" dragon-punch. Its shortcut is diagonal-based: `f, df` (down skipped entirely) comes out as a Shoryuken, which is why players eat accidental DPs walking up to throw.

- `dp_double_tap = False` — SFIV's DP leniency is the `df` shortcut, not the 3S/CvS2 double-tap. (If playtesting shows a held-down + double-forward input yields a DP, flip this.)
- `dp_skip_down = True` — `f, df` alone registers a Shoryuken. This False/True pairing is unique in the roster: `HSF2`/`SFA3`/`KOF98` are False/False, `SFIII3` is True/True.
- `lenient_diagonals = True` — `d, f` reads as a quarter circle; SFIV is a heavily-buffered engine.
- `charge_ms = 900` — SFIV's standard charge is ~55 frames; in the `HSF2`/`SFA3` range, not the shorter `SFIII3`.
- `charge_release_ms = 230` — SFIV's charge buffering / partitioning is notably forgiving; a hair more than `SFA3`.
- `negative_edge = True` — SFIV performs specials on button release.
- `motion_window_ms = 340`, `activation_window_ms = 200`, `step_gap_ms = 200` — interpolated toward `SFIII3`; the special buffer is wide and tolerant of a stray direction.
- `max_intermediate = 2`, `tail_states = 3` — junk tolerance like `SFIII3`.
- `rotation_window_ms = 550`, `rotation_slack = 3` — the 360/720 grapplers (Zangief, Hakan, T.Hawk, Hugo, Seth) are done leniently, often out of a jump.
- **Charge characters**: Balrog, Blanka, Chun-Li, Decapre, Dee Jay, E.Honda, Guile, M. Bison, Vega; partial — Gen (Jasen, Ouga) and Dudley (EX Thunderbolt only).
- **Headline quirk**: the only game here that gives a dragon punch for `f, df` while rejecting the hold-down-double-tap — the modern-buffer tradeoff, opposite to 3rd Strike on the double-tap axis but with the same diagonal forgiveness.

```python
Ruleset(
    motion_window_ms=340,
    activation_window_ms=200,
    step_gap_ms=200,
    max_intermediate=2,
    tail_states=3,
    lenient_diagonals=True,
    charge_ms=900,
    charge_release_ms=230,
    dp_double_tap=False,
    dp_skip_down=True,
    negative_edge=True,
    mash_count=5,
    mash_window_ms=600,
    rotation_window_ms=550,
    rotation_slack=3,
)
```

## Test seeds

Standard SF panel, so `harness.py`'s constants map straight through (`HP` = key `o`, `MK` = key `k`); no relabelling like the Neo Geo games.

- **ryu**: `QUARTER_CIRCLE_FORWARD_HP` → `Hadouken` (`qcf + P`), a sanity check against the other Capcom games. `DOWN_DOUBLE_TAP_FORWARD_HP` → `[]` — no double-tap DP, matching `sfa3` and **differing from `sfiii3`**, which gives `Shoryuken`. Custom `f, df + HP` (`press(FORWARD, 0)`, `press(DOWN, 60)` so forward-held + down resolves to df, `press(HP, 110)`) → `Shoryuken` — the `dp_skip_down` case, which yields nothing in `hsf2`/`sfa3`. A clean `f,d,df + HP` script → `Shoryuken`.
- **guile** (charge): custom — `press(BACK, 0)`, hold, `release(BACK, 960)`, `press(FORWARD, 970)`, `press(HP, 990)` → `Sonic Boom` (`Charge b,f + P`); the same shape with `DOWN`/`UP` and `HK` (key `l`) → `Flash Kick` (`Charge d,u + K`). `QUARTER_CIRCLE_FORWARD_HP` → `[]` (Guile has no `qcf`).
- **zangief**: custom 360 — `f, d, b, u + P` within ~500 ms → `Spinning Piledriver` (`Rotate 360 + P`); `rotation_slack = 3` means skipping four of the eight directions still counts. A clean `f,d,df + HP` script → `Banishing Flat`, **not** the SPD — a good check that the DP motion and the rotation don't cross-fire.
- **balrog** (charge): `Charge b,f + HP` script → `Dash Straight`; `Charge b,f,b,f + HP` → `Crazy Buffalo`. A `Charge b,df + HP` script (`press(BACK, 0)`, hold, `press(DOWN, 950)` and `press(FORWARD, 955)` for db then f, `press(HP, 975)`) should produce **nothing** — `(b,df)` is not a `_CHARGE_TABLE` key, the concrete example of this game's non-trainable slice.
