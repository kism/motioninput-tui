---
game: martmast
panel: snes-four
closest_parser: sfa3
predicted_trainable: 76
model: Claude Sonnet 5
---
# Martial Masters — brief

A weapon-fighting arcade game on a four-button panel (light/heavy punch, light/heavy kick, no mediums) whose headline quirk is that every character carries an identical templated pair of two-button "Shadow" EX specials (`qcf + LK+HP`, `qcb + LK+HP`, plus the shared `hcf + LP+LK` "Stagger Grab") laid over an otherwise ordinary SF-dialect motion set with no charge characters at all.

## Roster

- **12 characters**, ungrouped (no teams): Master Huang, Drunk Master, Scorpion, Crane, Red Snake, Ghost Kick, Monkey Boy, Tiger, Monk, Reika, Lotus Master, Saojin. This is the guide's full `3. Characters` section — there is no alternate-style/hidden-character prose to skip, and the `Sections` table of contents (~line 8-31) is the only thing that looks like a character list and isn't one.
- **Name overrides**: none needed — all twelve are plain ASCII, already the display form. Worth a manual double-check at implementation time against the rest of the roster in `datagen/names.py`: `Scorpion`, `Tiger`, `Crane`, and `Monk` are generic enough names that another game already loaded into the trainer could plausibly collide on the same `character_key()`; I can't confirm either way without the other rosters' full name lists in front of me.
- **Heading form**: a fixed three-line banner, no variants across all twelve —
  ```
  *******************************************************************************
  * 3.1 Master Huang                                                            *
  *******************************************************************************
  ```
  i.e. an asterisk rule of ~79 `*`, a `* <section#> <Name>` line right-padded with spaces to a matching `*`, then the same rule again. `common.DASHED` (which requires `[-]{10,}`) does not match this — it needs its own asterisk-rule regex.

## Guide anatomy (for the parser)

- **Move-list section**: from the bordered `3. Characters` heading (`===` rule / `3. Characters` / `===` rule, ~line 136) to the next top-level `===`-bordered heading after Saojin's `Supers` block (~line 1290). `3. Characters` also appears unbordered in the `Sections` table of contents (~line 14) — take the bordered occurrence, same disambiguation `DASHED` gives the other parsers.
  - Note: the guide's own numbering is inconsistent between the TOC (which lists `4. Codes` then `5. Conclusion`) and the body, which goes straight from Saojin's `Supers` to a heading literally reading `4. Conclusion` — there is no separate "Codes" section body in the file. Match the end marker on the literal heading text as written (`Conclusion`), not on an assumed section number.
- **Character heading**: `^\*{20,}\s*$` / `^\*\s*3\.\d+\s+([A-Za-z][A-Za-z0-9' -]*?)\s*\*\s*$` / `^\*{20,}\s*$`. No subtitle or team-suffix variant.
- **Per-character blocks**, in this fixed order, each headed by `Title\n----` where the dash count matches the title's own length (`Throw`/5 dashes, `Colors`/6, `Supers`/6, `Basic Move`/10, `Shadow Moves`/12, `Command Moves`/`Special Moves`/13) — *not* `common.DASHED`'s 10+ requirement, since `Throw`, `Colors` and `Supers` fall under it. Unlike KoF '98 there is only **one** move list per character, not a terse-then-verbose pair:
  - `Colors` — cosmetic, **skip**. Its lines use single-space ` - ` separators, not the fixed-width multi-space gap the move lines use, so they're unlikely to false-match, but the state machine should still gate move-collection on one of the six headings below being active rather than starting at the character banner.
  - `Throws`/`Throw`, `Basic Moves`/`Basic Move`, `Command Moves`, `Special Moves`, `Shadow Moves`, `Supers` — all worth parsing. A block ends at the next heading, the next character banner, or (for Saojin) the `4. Conclusion` marker.
- **Dialect**: the same hybrid SFA3 writes — `qcf + P` shorthand alongside fully spelled DP shapes (`f, d, df + K`, `b, d, db + P`). `_SHORTHAND`/`_WORD_DIRECTIONS` in `normalise.py` already handle both halves of this without changes. `sfa3.py` is the closest seed for the parser's state machine, though the header/column format below is novel enough to need new code, not a copy.
- **Line-level quirks**:
  - **Three columns, not two.** Every move line is `Name   Command   Description`, e.g. `Grasshopper               qcf + K                  LK=short, HK=far; must be blocked low`, with the description wrapping onto further-indented continuation lines. `common.split_name_command` only does a two-way split and would swallow the description into the "command" string. The martmast parser needs its own three-way split (`MULTI_SPACE.split(line, maxsplit=2)`, keep the first two parts, discard the third), and must recognise a continuation line by its deep indentation (aligned under the description column) so it isn't mistaken for a new move.
  - **Indented follow-ups carry no marker in the command text.** `Grasshopper`'s `Air Axe Kick` follow-up is written as `  Air Axe Kick           d + K                    Grasshopper must connect...` — the "must connect to perform this follow up" qualifier lives only in the description column being discarded above, and the command itself (`d + K`) is a perfectly ordinary `_UNSUPPORTED`-passing HOLD command. Unlike KoF '98's inline `X + P from Aragami` phrasing, there is nothing in the command text for `_UNSUPPORTED` to catch. The parser must treat the 2-space indent on the name itself as the "this is a follow-up" signal — structurally excluded (kept in the list, motion left `None`, per the `kof98._follows_on` precedent) rather than parsed as standalone. This hits every character to varying degrees: Master Huang's `Whirlwind Kick → Heavy Axe → High Kicks → Final Kick` chain alone is three follow-ups; Scorpion, Tiger, Monk, Crane, Monkey Boy, Reika, Red Snake, Lotus Master, and Ghost Kick each have one to four. Saojin has none.
  - **Unspaced `/` alternatives.** The legend defines `/` as "Or", and most of the guide writes it spaced (`LP+HK / LK+HK`), but several lines don't: `d/u + LP/LK/HP/HK` (the per-character "Pursue Attack", one per character), `qcf + P/LK` (Monkey Boy's Fruit Toss), `qcf + P/K` (Monk's Cauldron Drop). `normalise._parse_buttons`/`_direction_tokens` both split alternatives on `" / "` (spaced) — a bare `/` isn't recognised as a separator at all. Concretely, `qcf + P/LK` today would silently keep only the `LK` alternative and drop the `P` one entirely (`_BUTTON_TOKEN.findall("p/lk")` finds both tokens, but `p` isn't a key in `_SPECIFIC_BUTTONS`, so it's filtered out before the alternative-choice logic ever runs). The martmast parser should normalise every `/` in a command to `" / "` before calling `parse_command`, the same way `_strip_noise` already turns the word `"or"` into a spaced `/`.

## Notation & engine fit

- **Buttons `LP, HP, LK, HK`**, plus generic `P`/`K` — a strict subset of the Street Fighter six with no mediums, spelled exactly the way `normalise._BUTTON_TOKEN`/`_SPECIFIC_BUTTONS` already expect. **No button-family remap layer is needed** (no `kof98._neo_buttons` equivalent): the guide never writes `MP`/`MK`, so `parse_command` simply never emits them.
- **Panel: `snes-four` (`SNES_FIGHTER`)** — its two-per-row `(LP, HP)` / `(LK, HK)` shape matches this game's real four buttons exactly, and Sailor Moon S is already live proof this works with zero extra code: `ButtonRequirement(PUNCHES, 1)` for a bare `P` still resolves correctly even though `MP` has no key bound on this layout, because the recogniser only asks whether a *pressed* button is a member of the allowed set. `harness.py`'s own comment already anticipates this: `HP` in the shared scripts is key `o`, which is unbound on `SNES_FIGHTER` (only `u`/`i` are bound, to `LP`/`HP`).
- **Token collisions: none.** `LP/HP/LK/HK/P/K` never spells a direction token, unlike the Neo Geo games where `B`/`D` clash with `b`/`d`. No case-sensitivity trick is required here.
- **Motion not in `_MOTION_TABLE`**: `b, d, df` — Monkey Boy's `Monkey Stomp` and `Air Monkey Stomp` (2 moves), a DP-shape that ends on down-forward instead of down-back, distinct from both `DP` (`f,d,df`) and `RDP` (`b,d,db`). Everything else in the guide — `qcf`/`qcb`/`hcf`/`hcb`, `f,d,df`/`b,d,db`, the doubled supers (`qcf,qcf` → `QCF_X2`, `qcb,qcb` → `QCB_X2`), and the compound `hcb, f + P` (`Butterfly Strike`, `Heart Punch`, `Ruthless Strangle`) — already resolves to an existing `MotionKind` (`HCB_F`) with no table changes.
- **Category-override needed for `Supers`.** Most supers are doubled motions (`QCF_X2` etc., already in `SUPER_KINDS`), but at least one — Lotus Master's `Tower Of Flames`, `hcb + P` — is a *plain* single half-circle, which `categorise()` would default to `Category.SPECIAL`. The parser needs the same explicit-category-per-heading pattern `sfiii3.py`/`kof98.py` use, passing `Category.SUPER` for anything under a `Supers` heading regardless of what `categorise()` guesses from the motion alone.
- **Air-only moves use a trailing marker, not a leading one.** `Drill Kick — hcf + K in air` and `Air Sneaky Dart — qcb + P/LK in air` put "in air" at the *end* of the command; `normalise._detect_air`'s `_AIR_PREFIX` only matches a leading `In air,`. These moves' motions still parse correctly, but the resulting `MotionSpec.air` stays `False`, so the trainer will accept them on the ground too. Small, known gap — not worth a `normalise.py` change for two moves, but worth listing rather than silently shipping.
- **One structural mis-parse to flag, not fix**: Drunk Master's `Drunken Combo — HP, HP, HK, HP` is a four-press normal-attack chain (a "target combo"), which the engine has no model for. Today it would parse as `ButtonRequirement({HP, HK}, count=2)` — "press HP and HK together" — which is wrong, not just unrecognised. One move, not worth a table change; call it out as a known bad entry if `--show-skipped` doesn't catch it.
- **Predicted trainable ~76%.** Hand-tallying two characters end to end: Master Huang comes out around 20/31 (65%, an unusually follow-up-heavy special-move tree), Scorpion around 17/23 (74%), Saojin — who has zero indented follow-ups — around 18/21 (86%). The drags, in order of size: indented follow-up chains (correctly excluded once the parser tracks indentation — the single biggest category), the per-character "Pursue Attack" (`d/u + LP/LK/HP/HK`, correctly untrainable even after the `/`-spacing fix, since it degrades to "no direction, one of four buttons" which is below the two-button threshold), single-button `Basic Moves` with no direction, the `b,d,df` gap (2 moves), and the one target-combo mis-parse.

## Ruleset rationale

No decompilation and no numeric claims in the guide itself (no double-tap DP shorthand, no stated buffer windows, no charge notation at all), so this sits close to `SFA3`/`HSF2` rather than `SFIII3` — there is nothing here that argues for Third Strike's leniency, and Capcom-specific mechanics shouldn't be assumed just because the dialect looks similar.

- `dp_double_tap = False`, `dp_skip_down = False` — every DP-shaped special is always written as the full three-step `f,d,df` (or `b,d,db`); the guide never abbreviates one.
- `lenient_diagonals = False` — same call as Sailor Moon S: the guide spells `qcf`/`qcb`/`hcf`/`hcb` as their full diagonal-inclusive sequences and there's no evidence to turn this on.
- `half_circle_three_points = False` (the dataclass default) — no evidence of Third Strike-style leniency here either.
- `charge_ms` / `charge_release_ms` left at the dataclass defaults — **inert for this roster**: none of the 12 characters has a single charge move.
- `negative_edge = False` — no evidence either way; the dataclass's own rule is that this only turns on with real figures behind it.
- **Charge characters**: none.
- **Headline quirk**: a cast-wide templated 2-button EX layer. Every character has the *same* two buttons (`LK+HP`) and the *same* three motion shapes for their meter specials — `qcf + LK+HP`, `qcb + LK+HP`, and the shared `hcf + LP+LK` "Stagger Grab" — which is a different lesson than KoF's per-character EX inputs: here the trainee learns "same two buttons, different circle," cast-wide.

```python
Ruleset(
    motion_window_ms=300,
    activation_window_ms=150,
    step_gap_ms=170,
    max_intermediate=1,
    tail_states=2,
    lenient_diagonals=False,
    charge_ms=900,
    charge_release_ms=200,
    dp_double_tap=False,
    dp_skip_down=False,
    negative_edge=False,
    mash_count=5,
    rotation_window_ms=500,
    rotation_slack=2,
)
```

## Test seeds

`SNES_FIGHTER` breaks the shared `HP`-pressing scripts outright — `HP` in `harness.py` is key `o`, unbound on this panel (only `u`→`LP`, `i`→`HP` are bound). Use `SNES_HP` (`"i"`) in a custom script wherever a shared script presses `HP`. The `MK`-pressing scripts (`HALF_CIRCLE_SKIPPING_DOWN_MK`, `HALF_CIRCLE_THROUGH_DOWN_MK`) are usable as-is by coincidence: `MK`'s key `"k"` is the same physical key `SNES_FIGHTER` binds to `HK`.

- **scorpion**: `HALF_CIRCLE_SKIPPING_DOWN_MK` (reused verbatim) → `[]`. `HALF_CIRCLE_THROUGH_DOWN_MK` → `Desert Crawl` (`hcf + K`). Since `half_circle_three_points=False` here, the "skipped down" version must fail exactly the way it does in `SFA3`/`HSF2` — this is the clean same-script-different-answer-than-3rd-Strike case.
- **master-huang**: a custom `DOWN_DOUBLE_TAP_FORWARD` script ending in a press of `SNES_HP` instead of `HP` → `[]` (no DP shortcut here, same as `SFA3`/`HSF2`, unlike `USFIV`/`SFIII3`). A clean `f, d, df` + a kick key → `Nimble Knee`.
- **drunk-master**: a custom script shaped like `HALF_CIRCLE_BACK_FORWARD_HP` (`f, df, d, db, b, f`) but ending in `SNES_HP` → `Butterfly Strike`, exercising the `HCB_F` motion kind the guide's `hcb, f + P` phrasing produces.
- **lotus-master**: a custom plain half-circle-back script (`f, df, d, db, b`) ending in `SNES_HP` → `Tower Of Flames`. This is the one that only comes out right if the parser applies the `Supers`-heading category override — by motion kind alone (`HCB`, not `HCB_X2`) it would otherwise be mis-filed as a `Special`.
