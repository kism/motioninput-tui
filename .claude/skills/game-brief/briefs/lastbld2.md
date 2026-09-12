---
game: lastbld2
panel: neo-geo
closest_parser: kof98
predicted_trainable: 54
model: Claude Sonnet 5
---
# The Last Blade 2 — brief

SNK's 1998 Neo-Geo weapon fighter: a four-button panel where `D` is a *deflect* button, not an attack, and almost every DM is a long single-roll motion (`d,db,b,db,f`, `f,b,db,d,df,f`) that no Street Fighter game uses.

## Roster

- **17 playable characters** (the guide has 18 `+---+` headings; see the Kaede skip below). No teams — list flat: Kaede, Moriya Minakata, Yuki, Akari Ichijo, Juzo Kanzaki, Amano Hyo, Washizuka Keiichiro, Genbu no Okina, Lee Rekka, Zantetsu, Naoe Shigen, Mukuro, Shinnosuke Kagami, Hibiki Takane, Kojiroh Sanada, Setsuna, Musashi Akatsuki.
- **Skip**:
  - `    KAEDE (Awakened)` (heading ~line 90). It is the unlockable alternate form of Kaede, and `character_key()` yields `kaede` for both it and `    KAEDE (original)` (~line 530) — a collision like kof98's EX/Omega dupes. Parse `(original)` as `kaede`, drop `(Awakened)`. (Alternative: special-case Kaede to keep the parenthetical → keys `kaede` / `kaede-awakened`.)
  - There is **no table of contents** in this guide, so unlike sfa3/sfiii3 there is no start-marker to disambiguate.
  - The `SYSTEM & CONTROLS` block (lines ~35–77): the button legend, `Throw: C + D`, Repel lines, and `Activate Combo Special ... d, d + A or B` (line ~53) all sit before `MOVELISTS` (line 81); a parser anchored to the first `+---+` (line 89) excludes them automatically.
- **`datagen/names.py` overrides**: none required. No LB2 name collides with another game's roster, and the caps headings title-case cleanly. (Optional long-vowel polish: `akari-ichijo` → "Akari Ichijou", `amano-hyo` → "Amano Hyō" — not necessary.)
- **Heading shape**: a caps name on its own line with `+---------------------+` immediately above and below. That rule matches `common.DASHED` (both `+` and `-` are in its char class), so `sfiii3._match_header` works as-is. Variants: trailing parenthetical `(Awakened)` / `(original)` (Kaede only), and a trailing author aside ` - actually Kaori Sanada` (Kojiroh) / ` - DC/Neo Geo CD port in 2 player mode` (Musashi) — strip trailing ` (...)` and ` - ...`.

## Guide anatomy (for the parser)

- **Move-list section**: from `      MOVELISTS` (line 81, boxed by `o--------------------o` on 80/82), or equivalently the first `+---------------------+` (line 89), to `       CREDITS` (~line 557) — the same `.strip() == "CREDITS"` anchor `kof98._section` already uses. No ToC occurrence of either marker.
- **Character heading**: `^\s*([A-Z][A-Z0-9 .'!"-]*?)\s*(?:\([^)]*\))?\s*(?:-\s+.*)?$` on a line with `DASHED` above and below. Reuse `sfiii3._match_header`; the `SPECIAL MOVES` / `SUPER MOVES` box lines are between `o---o` rules (not `DASHED`) so they are not mistaken for headings.
- **Block to parse**: everything from the header to the next `DASHED` / `CREDITS`. There is only **one** list per character (no terse/verbose split). Category comes from the boxed heading lines `SPECIAL MOVES` (~line 94) and `SUPER MOVES` (~line 107) — reuse `kof98._HEADINGS`, but only those two keys occur (no `THROWS` / `COMMAND MOVES`).
- **Move lines**: `Name: command`. Split on the **last** colon (`kof98._move`) — names carry colons, e.g. `Futtobashi: Kattobashi: d, df, f + C` (Juzo).
- **Notation dialect**: directions spelled `d, df, f`, comma-separated, lowercase (Alpha 3 / KoF style, not HSF2's `D, DF, F`); charges as `b~f` / `d~u` / `f~b`; super repeats as `(d, df, f)x2` and `(f, df, d, db, b) x2`; buttons `A B C D`. **Closest parser: `kof98`**, plus its `neogeo` helper for the panel remap and the `~` / `(…)x2` dialect.
- **Line-level quirks**:
  - Follow-ups are written `Name: <ParentMoveName>, <motion> + <btn>` — e.g. Akari `Anaguma no Fudoshi Nugi: Ibisha Anaguma, d, df, f + B`, Washizuka `Shashiki: Rouga, d, db, b + C`. `_UNSUPPORTED` does **not** catch these (no `from`/`then`/`after`), so `normalise` strips the parent words and reads the motion → **spurious trainable**. Extend `kof98._follows_on` to also test the command's leading `Capitalized, ` clause against earlier move names. ~47 moves.
  - Genuine `then` / `after B version` chains (`Shinmei Kuga: … then f, d, df + B after B version`, ~line 99; `Enryu Haibi: … after B version`) are caught by `_UNSUPPORTED`, correctly non-trainable — but the base DP/HCF input is lost with them.
  - `during super cancel` (Kaede SDMs — `during`), `(delayable)`, `(up to 3 times)`, `(in speed mode or EX only)` — parentheticals stripped.
  - Condition prefixes: `close,` (`Shinmei Arashiuchi: close, b, db, d, df, f + C`), `when close` (Musashi `Makura Nidan`), and `in air` — which is a *suffix* here (`… + A or B in air`), so `_strip_noise` leaves it and the move parses as its ground motion; the guide never uses a leading `In air,`.
  - Typos that break matching: `Iwakudai` for Iwakudaki, `Konogosai` for Kongosai (defeats the `_follows_on` substring test → spurious parse), `d, db, db` for `d, db, b` (Juzo `Bunnage`), `Hsha` for Hisha. Expect a handful of "unrecognised motion".
  - `+ Start` / `hold Start` / `hold A then release` (Amano `Chou Jou Hatsu`, Lee `Ibuki`, Hibiki `Sanae…`, Musashi `Shuuchuu`) — dropped cleanly by `_UNSUPPORTED` (`\bstart\b`, `then`).

## Notation & engine fit

- **Buttons `A B C D`**, panel `NEO_GEO` (`buttons.py` key `neo-geo`). Semantics differ from every Neo Geo game already in the repo: `A` weak slash, `B` strong slash (lines 35/37), `C` kick (39), **`D` is Repel/deflect — not an attack** (lines 43–46). `C + D` is throw (line 47). Attacks live on only three of the four buttons; `D` appears in a move command only in `C + D` air moves (Naoe `Ruri Sai`, Kaede `Ittou Kaminari Ikadzuchi`).
- **The panel needs the parser-side remap**, exactly as `kof98`: the recogniser matches `Button` identity, not a punch/kick family, and `normalise` only emits the SF six. So the parser must translate each command to SF notation for `parse_command`, then map the resulting `ButtonRequirement` back onto `A B C D` with an explicit label — reuse `datagen/parsers/kof98.py`'s Neo Geo remap (`neogeo.to_shorthand` / `to_neo_panel` / `_neo_buttons`). `ALL_BUTTONS` stays the SF six. Suggested LB2 table: `A→LP`, `B→HP`, `C→LK`, `D→MK`; `A or B` → `{LP,HP}` (either slash), `A or B or C` → `{LP,HP,LK}` (any attack), `A + B` → count 2, `B + C` → `{HP,LK}` count 2.
- **Token collision**: button `B`/`D` vs direction tokens `b`/`d`. The guide is consistent — directions always lowercase (`d, db, b`), buttons always uppercase (`+ B`) — so the remap regex is case-sensitive (as in kof98). `A`, `C`, `f` never collide.
- **`~` charge and `(motion)x2` are not handled by `normalise` itself**: `_strip_noise` deletes `(...)` *before* it reads directions, so `(d, df, f)x2` loses its motion unless `neogeo.to_shorthand` de-parenthesises it first (it already does for the KoF '98 / 2001 guides). Same for `b~f`/`d~u`→charge and `f~b`.
- **Motions NOT in `normalise._MOTION_TABLE` / `_CHARGE_TABLE`** (skipped as "unrecognised motion"):
  - `d,db,b,db,f` (qcb, then back out to forward) — the standard DM/SDM roll; **~10 moves** (Yuki, Akari, Lee ×2, Shinnosuke, Hibiki, Kojiroh ×2, Kaede ×2).
  - `f,b,db,d,df,f` (forward, then half-circle-forward) — the other DM roll; **~8 moves** (Moriya ×2, Genbu ×2, Zantetsu, Shinnosuke, Hibiki, Kojiroh `Shikku Satsu`).
  - `b,db,d,df,f,b` (hcf then back) — **1** (Naoe `Inga Ouhou`).
  - `f,b` charge (from `f~b`) — **1–2** (Juzo `Iwakudaki` + `Tetsu Atama`); `_CHARGE_TABLE` has `("b","f")` only.
  - `df,df` (**1**, Amano `Shougi Doushi`), `f,db,f` (**1**, Amano `Suzume Sashi`), `f,b,f` (**1** + follow-ups, Zantetsu `Kagehoushi`), `f,b,hold f` (**1**, Mukuro `Jiname Suberi`).
  - three-way single-direction alt `b / f / d + B` (**1**, Kaede Awakened `Ittou Raitei` — skipped char).
  - Note `(d,df,f)x2` (QCF_X2), `(f,df,d,db,b)x2` (HCB_X2), `(b,db,d,df,f)x2` (HCF_X2) and `f,df,d,db,b,f` (HCB_F) **are** in the table — Setsuna's `Mumei - Kyoku`, Musashi's `Gorin Tsurane`, etc. are fine.
  - **Since added** as `MotionKind.QCB_DB_F` and `MotionKind.F_HCF`, with a matcher case each — 19 moves here, and 49 across the four SNK rosters, which is what settled it. Unlike the `qcf,hcb` work done for kof98 the shorthand expander does not produce these, so it was real matcher work rather than a dict line.
- **Predicted trainable ≈ 54%** (`datagen --show-skipped`), assuming the leading-parent follow-up check is added and no new `MotionKind`s. (Without the follow-up fix the parser over-reports ~75% by reading the motion out of follow-up commands.) Below 80% because:
  - every character's `Pounce:` line has no directional and a single-button choice → "no directional or multi-button requirement" (**17**);
  - the two unsupported DM rolls plus the smaller motion gaps (**~24**);
  - genuine follow-up / stance chains — the Kasumi, Rouga, Kongosai/Kai/Aku, Gaiki DorotaBou trees and `then`/`after` variants (**~47**);
  - `+ Start` taunts, single-purpose odd motions, guide typos (**~8**).
  - Command grabs are **not** a problem here (unlike kof98): they are written `close, <hcf|hcb> + C` and keep a real motion. With the two rolls added, expect ~63%.

## Ruleset rationale

LB2 sits between `SFA3` and `SFIII3` and leans `SFA3`, tracking its `KOF98` sibling on the same panel: generous SNK buffering, but a genuine `f,d,df` for the DP-motion specials (`Ittou Shingetsu`, `SouKa`, `Yurashi`, `Chouka Tairyou`, …) — no Capcom "hold-down, double-tap-forward" shortcut and no `f,df` shortcut. Stricter than `HSF2` only in that diagonals may be skipped; nowhere near `SFIII3`'s junk tolerance.

- `dp_double_tap = False` — SNK; the DP is `f,d,df` and nothing else.
- `dp_skip_down = False` — same.
- `lenient_diagonals = True` — SNK buffering; `d,f` reads as a quarter circle (matches `kof98`, `samsho2`, `samsh5sp`).
- `charge_ms = 850` — Washizuka's `b~f` / `d~u`; interpolated to the `kof98` value. **Exact LB2 charge frames not confirmed** — flag for verification.
- `charge_release_ms = 220` — as `kof98`.
- `negative_edge = True` — KoF-era SNK MVS title; this field is display-only (the terminal can't see releases). **Low confidence** — could be `False` like the Samurai Shodown pair.
- `motion_window_ms = 320`, `activation_window_ms = 160`, `step_gap_ms = 180`, `max_intermediate = 1`, `tail_states = 2` — interpolated between `SFA3` and `SFIII3`, identical to `kof98`; nothing about the 1998 engine argues for tighter windows.
- rotation fields: defaults — **there is no 360 or 720 anywhere in the game**, so they never apply.

**Charge characters**: Washizuka Keiichiro (`b~f`, `d~u`). Lee Rekka has one (`Ensenshou`, `d~u`). Juzo Kanzaki has a reverse `f~b` (`Iwakudaki`) the engine cannot model. Everyone else is motion-only.

**Headline quirk this game teaches**: nearly every DM is a long, clean single-roll motion from neutral — `d,db,b,db,f` or `f,b,db,d,df,f` — a shape no Street Fighter game uses; paired with zero DP leniency and zero rotation moves, this is the "long roll, strict execution" corner of the set.

```python
Ruleset(
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
    mash_window_ms=600,
    rotation_window_ms=500,
    rotation_slack=2,
)
```

## Test seeds

`harness.play_as` lays the game panel onto `HITBOX`, so the keys become `u`=A, `i`=B, `o`=C, `p`=D. `QUARTER_CIRCLE_FORWARD_HP` / `DOWN_DOUBLE_TAP_FORWARD_HP` therefore press key `o` = **C (kick)**, and `HALF_CIRCLE_*_MK` press `k` = **B (strong slash)**. Most LB2 specials are `+ A or B`, so the `..._MK` (B) scripts fire them and the `..._HP` (C) scripts mostly do not — use a custom `+ B` (key `i`/`k`) script per character.

- **moriya-minakata** — `DOWN_DOUBLE_TAP_FORWARD_HP` → `[]` (no DP shortcut; the same script is a dragon punch in `sfiii3`/`usfiv`, nothing in `sfa3`/`hsf2`). Custom clean `f, d, df` then B (`i`) → `Ittou Shingetsu`. Custom `d, db, b` + B → `Ittou Oboro Chuudan`. Custom `f, b, db, d, df, f` + A+B → `Kassatsu Izayoi Gekka (DM)`, on the `F_HCF` motion added since this brief was written.
- **washizuka-keiichiro** — pure charge-timing seed (no SF character does this): hold `BACK` ~1000 ms then `FORWARD` + B (`i`) → `Shikku Satsu`; hold `DOWN` ~1000 ms then `UP` + B → `Koku Satsu`; hold `BACK` only ~300 ms then `FORWARD` + B → `[]` (exercises `charge_ms=850`).
- **yuki** — custom `d, df, f` + B (`i`) → `HyouJin`; the same qcf done with the "HP" key (`o` = C) fires nothing, which is the panel remap in one test. Custom `b, db, d, df, f` + C (`o`) → `HyouKyou`. `DOWN_DOUBLE_TAP_FORWARD_HP` → `[]`.
- **genbu-no-okina** — custom `b, d, db` + A (`u`) → `Mukuyu Jin`, a true reverse dragon punch (`_MOTION_TABLE[("b","d","db")] = RDP`), rare in the SF sets and clean here. Custom clean `f, d, df` + A → `Chouka Tairyou`. Custom `f, b, db, d, df, f` + A+B → `[]`, skipped (`Genbu no Hoko`).
