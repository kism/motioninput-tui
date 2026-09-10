---
game: hsf2
panel: street-fighter
closest_parser: hsf2
predicted_trainable: 86
model: Claude Sonnet 5
---
# Hyper Street Fighter II: The Anniversary Edition — brief

A 17-fighter compilation that puts every SF2 revision on one select screen; its headline input quirk is that it is the *literal* reference point — a dragon punch is a genuine `F, D, DF`, diagonals are mandatory, and releasing a button does nothing.

**Read this first:** this game already ships as `HSF2` in `src/motioninput_tui/games/rulesets.py`, with `src/motioninput_tui/datagen/hsf2.py` and `references/hsf2.txt`. The FAQ below is in exactly that parser's dialect (`- Ryu -` headers, `Fireball       - D, DF, F + any Punch` move lines, `Combos:`/`Notes:`/`Best version:`/`Basic Strategy:` stop words). Whoever picks this up is doing a re-parse / regression pass against an existing `Ruleset`, not a greenfield game. Everything below is written so the existing parser can be checked line-by-line against this specific guide; line numbers are eyeball estimates against the 1076-line file, marker text is exact.

## Roster

- **17 characters**, a single flat list under `Move List:` (line ~87), first header `- Ryu -` at line ~90. No team grouping. In guide order: Ryu, Ken, E.Honda, Chun-Li, Blanka, Zangief, Guile, Dhalsim, T.Hawk, Cammy, Fei Long, Dee Jay, Balrog, Vega, Sagat, M.Bison, Akuma.
- **Skip:**
  - The whole preamble before `- Ryu -` (lines 1–~89): *Joystick Abbreviations*, *Game Abbreviations*, *Game mechanics*, *Terminology*, *How to pick Old Characters:*. `hsf2.py` ignores it because `collecting` is `False` until a header fires.
  - Per-character `Combos:` / `Notes:` / `Best version:` / `Basic Strategy:` blocks — ended by `hsf2._STOP`.
  - *How to pick Akuma:* prose inside Akuma's block (~line 1040); it lands after `_STOP` has already tripped on `Notes:`, so no special handling.
  - The `S P E C I A L    T H A N K S` / Copyright footer (~line 1055).
  - **There are no alternate-style character entries to skip.** "Old" (`O.`) versions are only mentioned in prose ("Old Ken has a superior LP Dragon Punch", "Best version: Old Sagat") — they get no headers and no move lists. Unlike SFA3 (ISM column) and KOF98 ("Style Character"), every character appears exactly once and every version's moves are merged into one block with `(ST only)` / `(SSF2 / ST only)` tags. There is also **no table of contents**, so none of the `starts[-1]` / second-occurrence logic the other parsers need applies here.
- **`datagen/names.py` overrides:** none. All 17 headings are conventional Western SF2 names. `finish_character` only `.title()`s all-caps names, and none of these are all-caps, so `E.Honda`, `T.Hawk`, `M.Bison`, `Chun-Li`, `Fei Long`, `Dee Jay` pass through unchanged (keys `e-honda`, `t-hawk`, `m-bison`, `chun-li`, `fei-long`, `dee-jay`). If the repo's existing `names.py` already maps the shared shoto/boxer/claw keys for cross-game display consistency, reuse those entries as-is; this guide introduces no new spellings.
- **Heading shape:** `^- ([A-Z][A-Za-z0-9.'\- ]{1,20}) -\s*$` on one line, an 80-char dashed rule on the next (`hsf2._HEADER` + `common.DASHED`). No subtitles, no team suffixes, no variant forms.

## Guide anatomy (for the parser)

- **Move-list section:** `hsf2.py` has no section bounds — it scans the whole file. Human anchors: `Move List:` (line ~87) → the last character (Akuma) is closed by `finish_character` at EOF; content stops before the `S P E C I A L    T H A N K S` banner. `_STOP` (`Combos|Notes|Best version|Basic Strategy|How to pick`) closes each character's move block.
- **Character heading:** as the regex above; always paired with a following `DASHED` line, which `hsf2.parse` checks explicitly (`DASHED.match(lines[index + 1])`).
- **Block to parse:** the terse dash-list immediately under the header rule, up to the first `Combos:`/`Notes:`. There is exactly **one** move list per character — no verbose "Translation:/Move Command:" second list (contrast KOF98). Moves come in two groups separated by a blank line — base moves, then edition-gated additions — but all are `Name  - command` shaped and all under the same block.
- **Notation dialect:** directions spelled as letters (`D, DF, F`, `B, DB, D, DF, F`, `F, D, DF`, `DB, D, DF, F, UF`); charges as `Charge Back for 2 secs, Forward` and `Charge DB for 2 secs, DF, DB, UF`; also the bare **`Back for 2 secs, Forward`** form with no word "Charge" (Chun-Li, ~line 262), which `normalise._SECONDS` still catches. Buttons: `any Punch`, `any Kick`, `all Punches`, `all 3 Punches`, one `any K` abbreviation (E.Honda Butt Slam), specific `F + MP`. Repeat marker `D, DF, F x 2`. Rotations `360 + P`, `720 + any Punch`. **Closest existing parser: `hsf2` itself** — this is the Hyper SF2 spelled-out dialect and `datagen/hsf2.py` already targets this exact layout.
- **Line-level quirks:**
  - **Continuation lines are indented** under the previous command (`(ST only)` tails on Blanka Ground Roll and Sagat Rolling Izuna Drop; the second `Backflip` line for Vega). `hsf2.parse` drops any line where `_MOVE` fails to match, and separately `continue`s on `line.startswith(" ")`. Effect: wrapped tags are harmlessly lost, and Vega's indented `Backflip - Press all 3 Punches` variant is silently dropped (it is a duplicate name anyway).
  - **Follow-up phrasing:** `after Head Press, press any Punch` (Bison Skull Diver v1), `during Hooligan press Kick` (Cammy Throw / Cancel) — caught by `normalise._UNSUPPORTED` (`after`, `during`), correctly non-trainable.
  - **Context prefixes:** `in air,` (T.Hawk Hawk Dive / Body Press, Dee Jay Knee Shot) — `_strip_noise` removes `in air,` and `_AIR_PREFIX` sets the air flag; `from distance,` (Zangief Flying Powerbomb) — *not* unsupported thanks to `from (?!...distance)`; `close,` (Guile Downward Spin Kick) — stripped by `_QUALIFIERS`.
  - **Edition tags** `(ST only)`, `(SSF2 / ST only)`, `(SF2T and up)`, `(CE only)` are parentheticals, removed by `_PARENTHETICAL` before parsing. The parser keeps every version's moves in one flat list — expect ~7 moves per character, not the ~4 a single-edition list would give.
  - `(can be done in air ...)` on Ryu/Ken Hurricane and Akuma Fireball is deliberately ignored by `_detect_air`.

## Notation & engine fit

- **Buttons:** `LP MP HP` / `LK MK HK`, panel `STREET_FIGHTER` — the default `GameSpec.buttons`, nothing to set. **No panel translation.** This is the one game family `normalise` is natively written in; the Neo Geo `_neo_buttons` remap in `datagen/kof98.py` does not apply.
- **Token collisions:** none. `parse_command` lowercases everything, so direction letters `b/d/f/u` never collide with button tokens `lp mp hp lk mk hk p k`. `F + MP` → `f` (direction) + `mp` (button), clean.
- **Motions NOT in `normalise._MOTION_TABLE` / `_CHARGE_TABLE`** (skipped):
  - `F, DF, D` — Zangief Glow Hand → `f,df,d`, no key → "unrecognised motion" (**1 move**).
  - `B, DF, D, DF, F` — Akuma Red Fireball, a guide typo for `B, DB, D, DF, F` → `b,df,d,df,f`, no key (**1 move**).
  - `Charge Back … DF` — Balrog Dash Low → `b,df` charged, not in `_CHARGE_TABLE` (**1 move**).
  - `Back, Back` — Vega CE Backflip → `b,b`, and no button token at all (**1 move**).
  - `Back or Forward + <one kick/punch>` command normals — E.Honda Sweep; Guile Knee ×2, Downward Spin Kick, Spin Kick; Fei Long Forward Hop → `_direction_tokens` returns `[]` for the side choice and the lone button fails the multi-button test → "no directional or multi-button requirement" (**~7 moves**, four of them Guile's).
- **Predicted trainable ≈ 86 %** (~96 / 111). Above 80 %, so no deep structural gap. The shortfall is: (a) `b/f + single button` command normals the engine has no side-agnostic model for (~7); (b) real motions outside the tables — `f,df,d`, `charge b→df` (~2); (c) genuine follow-ups `after` / `during` (~3); (d) one guide typo. **Guile alone is 3/7 trainable (43 %)** and drags the average; the shotos, Sagat, T.Hawk, Dee Jay and Blanka are ~100 %.
- **The number is slightly optimistic** because several moves parse to a technically-present but loose motion and still count as trainable: Dhalsim Teleport → `DP`; Vega Izuna Drop / Rolling Izuna Drop and Cammy's Hooligan follow-ups keep only the charge/HCF stem; Dee Jay Hyper Fist → `MASH` (it is really a charge move whose "press P rapidly" tail wins mash detection); Balrog Turn Around Punch → `ANY` (a hold-and-release button move). Don't count these as correct in a spot-check.

## Ruleset rationale

This is `HSF2` — the strict end of the spectrum, stricter than `SFA3`, far stricter than `SFIII3`. Ground truth: Super Turbo / HSF2 has the tightest buffer of the four games (~1–3 frame leniency), no negative edge, no dragon-punch shortcut. Holding down and tapping forward gives a fireball or nothing, never a shoryuken — the guide writes `Dragon Punch   - F, D, DF + any Punch` in full (line ~94) and means it. I'm confident on the qualitative facts; the exact charge frame count I'd only pin to "roughly one second, longer than Alpha 3 or KoF" — the repo's existing "around 55 frames" note is a reasonable read, don't invent more precision.

- `dp_double_tap = False` — ST wants a real `f,d,df`.
- `dp_skip_down = False` — `f,df` alone is nothing.
- `lenient_diagonals = False` — `d,f` is not a shortcut; skipping `df` loses the fireball entirely.
- `charge_ms = 950` — ~55-frame charges, the longest on the roster (the FAQ's "for 2 secs" is shorthand, not literal); matches the shipping `HSF2`.
- `charge_release_ms = 180` — tight, stricter than SFA3's 200.
- `negative_edge = False` — ST has none. Balrog's Turn Around Punch is a charge-and-release *button*, not negative edge.
- `motion_window_ms = 250`, `activation_window_ms = 120`, `step_gap_ms = 140`, `max_intermediate = 1`, `tail_states = 2` — the strict interpolated values; clean motions, no junk mid-input.
- `rotation_window_ms = 450`, `rotation_slack = 2` — Zangief / T.Hawk 360s and 720s; ST is forgiving on rotation shape but the window is tighter than the lenient games.

**Charge characters:** E.Honda, Chun-Li, Blanka, Guile, Dee Jay, Balrog, Vega, M.Bison. Guile and M.Bison are the pure charge characters; Chun-Li and Blanka are hybrids (charge *and* mash/motion moves).

**Headline quirk it teaches that the others don't:** the fully literal read — strict `f,d,df` DP *and* mandatory diagonals *and* no negative edge, all at once. It is the "nothing is inferred" baseline the other three rulesets are measured against.

```python
Ruleset(
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
)
```

## Test seeds

- **ryu** (`hsf2/test_ryu.py`): `QUARTER_CIRCLE_FORWARD_HP` → `Fireball`. `DOWN_DOUBLE_TAP_FORWARD_HP` → `[]` — no DP shortcut, the canonical difference from `sfiii3` (where the same script yields a Shoryuken). A clean custom `f,d,df + HP` script → `Dragon Punch`.
- **guile** (`hsf2/test_guile.py`): custom — hold `BACK` ~1000 ms then `FORWARD` + `HP` → `Sonic Boom`; hold `DOWN` ~1000 ms then `UP` + `HK` → `Flash Kick`. Then a **~850 ms** back-hold + forward + HP → `[]` here, but the *same* hold would produce `Sonic Boom` in `sfa3` (`charge_ms=880`) and `sfiii3` (`800`) — a real per-game divergence. `QUARTER_CIRCLE_FORWARD_HP` → `[]` (Guile has no motion special; good negative test).
- **zangief** (`hsf2/test_zangief.py`): a 360 script (`f, d, b, u` + `HP` inside `rotation_window_ms=450`) → `Spinning Pile Driver`; a 720 script → `Final Atomic Buster`. `QUARTER_CIRCLE_FORWARD_HP` → `[]`. Do **not** seed `Glow Hand` (`F, DF, D`) — it is un-trainable.
- **chun-li** (`hsf2/test_chun_li.py`): hold `DOWN` ~1000 ms then `UP` + `MK` → `Spinning Bird Kick`. A custom back→forward half-circle + `HP` → `Fireball` — the parser reads her first `B, DB, D, DF, F + any Punch` as a plain `HCF`, so unlike any real Street Fighter shoto a half-circle-punch produces a projectile here; the down-skipping half-circle variant then rides the player's "relaxed half circles" setting. A rapid-`MK` mash script → `Lightning Kick`.
