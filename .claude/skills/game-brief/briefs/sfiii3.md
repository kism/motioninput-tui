---
game: sfiii3
panel: street-fighter
closest_parser: sfiii3
predicted_trainable: 88
model: Claude Sonnet 5
---
# Street Fighter III: 3rd Strike — brief

Capcom's last SF3, six-button Street Fighter panel; its headline quirk is auto-shoryuken — holding down-ish and tapping toward twice yields a dragon punch — plus EX moves on two buttons and equipped Super Arts, and a parry system the trainer cannot model.

## Roster

- **20 characters**, listed alphabetically (no teams), from section 2's `====`-boxed `2.  CHARACTER MOVELISTS` banner (~line 199): Alex, Chun-Li, Dudley, Elena, Gill, Gouki, Hugo, Ibuki, Ken Masters, Makoto, Necro, Oro, Q, Remy, Ryu, Sean, Twelve, Urien, Yang, Yun.
- Gill is a hidden character but has a **full move block in section 2**, so he is parsed like the rest; the "PLAY AS GILL" prose in section 3 is past the section end and ignored.
- **SKIP**: the `TABLE OF CONTENTS` (~line 32–100 — the entry line ` 2.  CHARACTER MOVELISTS` there is identical to the real banner, see below); section 1's `BASIC MOVESLIST` (universal throws/parries/dashes — it sits before the section start, do not fold it in); everything from `3.  SECRETS AND TRICKS` onward. In particular do **not** widen the section to reach the `[ NOTES ON USING ALL SUPER ARTS ]` table in section 4: those `qcb,qcb + P` super commands are a System Direction toggle, not the defaults.
- Per character, also skip `Target Combos:` / `Link Combos:` / `Combos:` blocks, the `-` note bullets, and the EX-use / defense-rating tables in the gameplay notes.
- **`datagen/names.py` overrides**: none. `character_key()` turns the all-caps headings into clean keys (`KEN MASTERS` → `ken-masters`, `Q` → `q`, `GOUKI` → `gouki`). Gouki is Akuma, but `gouki` collides with nothing, so no override is forced; add `gouki` → `Akuma` only if the project standardises on the Western name elsewhere.
- **Heading shape**: a name between two rules of ~72 dashes, `NAME` or `NAME, Title` — parser regex `^ ?([A-Z][A-Z0-9.'\- ]{0,30})(?:,\s*(.+))?$`. Variants: internal space (`KEN MASTERS`), single letter (`Q`), free-text title with lowercase and punctuation (`Q, Whose Existence is a Mystery`).

## Guide anatomy (for the parser)

- **Move-list section**: `SECTION_START = "2.  CHARACTER MOVELISTS"` (two spaces after the period) to `SECTION_END = "3.  SECRETS AND TRICKS"`. Both strings also appear in the table of contents; `sfiii3.py`'s `_section` deliberately takes the **second** occurrence of the start (the `====` banner, ~line 199) and the first end occurrence after it (~line 1500).
- **Character heading**: a `_HEADER` match sandwiched between two `DASHED` lines; `_match_header` additionally rejects `TABLE OF CONTENTS` and blank names. Title is the optional `, ...` capture.
- **Which block to parse**: the terse move list directly under the heading — `_MOVE = ^ {1,6}(?:(EX|III|II|I|any)\s+)?(\S.*?) {2,}(\S.*)$` (optional flag column, then fixed-width `Name  command`). It ends at `_STOP` (`Target Combos|Link Combos|Combos` + `:`) or the first `- ` note bullet. There is no separate verbose list here — 3S has only the one.
- **Notation dialect**: Alpha-3 shorthand — `qcf + P`, `hcb + K`, `f,d,df + P`, `Charge b,f + K`, `Charge d,u + P`, `qcf,qcf + P`, `Rotate 360 / 720 + P`, trailing `x1`/`x2`/`x3` stock counts. Prefixes `In air,`; suffixes `when close`, `(air)`, `(perform 2 times)`. Flag column `EX` / `I` / `II` / `III` / `any` (Super Arts). Closest existing parser is **`sfiii3.py` itself**, which was seeded from `sfa3.py` (same shorthand; SFA3's `XAV` ISM column is the analogue of the `EX/I/II/III` flag).
- **Line-level quirks**:
  - Follow-ups written as their own rows: `Press P during Ducking`, `...do nothing after Hyakki Shuu`, `...press K while in air`, `qcf + P from SA III`, `qcb + K, then same K...`. `normalise._UNSUPPORTED` catches `during`, `after`, `while`, `then`, and bare `from` — all fall out as "conditional or follow-up move".
  - `back-turned` moves (`Headbutt a back-turned opponent`, `Snake Fang a back-turned opponent`) — also `_UNSUPPORTED`.
  - Condition prefixes/suffixes: `In air,`, `When close,`, `Jump u or uf, d + HP` (the `_direction_tokens` "choice over the first token" path keeps `d`), `Jump against a wall, then press uf`.
  - `~` roll notation: `db~df + HP`, `while jumping, press ub~uf`. `_tokens_in` splits on `[,\s]+` only, so `db~df` is one unrecognised chunk → no tokens → skipped.

## Notation & engine fit

- **Buttons**: LP MP HP LK MK HK; panel `STREET_FIGHTER`. **No translation layer is needed** — unlike `datagen/parsers/kof98.py` and its `_neo_buttons`, the roster and `normalise` are already in this panel's vocabulary. EX moves (`qcf + PP`) and Super Arts read as ordinary `ButtonRequirement`s of count 2 / family.
- **Token collisions**: none in practice. Directions are lowercase (`f,d,df`); buttons are `P`/`K`/`LP`…`HK` and always carry a letter `_BUTTON_TOKEN` recognises. There is no `B`/`D` button on this panel to clash with the `b`/`d` direction tokens (that was the Neo Geo problem). The `EX`/`I`/`II`/`III` flag column is disambiguated by line-start anchoring and the 2-space gap before the name.
- **Motions NOT in `_MOTION_TABLE` / `_CHARGE_TABLE`** (skipped):
  - `d,d,d` — Gouki's Kongou Kokuretsu Zan (`d,d,d + PP`), ~1 move.
  - `~` rolls: `db~df`, `ub~uf` — Chun-Li's Suitotsu Da, Q's Tentou kara no Kyakubu Tsuugeki, Oro's 2 Dan Tobi, ~3 moves.
  - `uf,d` and `u/uf`-then-`df` two-token diagonals — Gouki's Tenma Kuujin Kyaku, Yang/Yun Raigeki Shuu (also `then`), ~3 moves.
  - `d / df + HP`, `b / f + HK` (choice-of-side, single button, no held direction) — Necro's Whip Straight, Hugo's Drop Kick, ~3 moves.
  - Buttonless air-dash / wall moves (`tap b,b / f,f`, `ub,ub`) — Twelve's Kokkuu family, ~2 moves.
  - **Not** a problem here: every Super Art is `qcf,qcf`, `qcb,qcb` or `Rotate 360/720`, all of which are in the tables. There are no compound super motions (`qcf,hcb` etc.), which is why 3S scores far above KoF '98's 63%.
- **Predicted trainable ≈ 88%** (~355/~400). Above the 80% line; the ~12% loss is entirely: genuine follow-ups and stances (`during`/`after`/`then`/`...`/back-turned — the largest bucket, ~40 moves), the `~` roll and two-token-diagonal commands above (~10), Kongou Kokuretsu Zan (`d,d,d`, 1). Two more parse but are semantically wrong and still count as trainable: Gouki's Raging Demon `LP,LP,f,LK,HP` collapses to a generic two-button `ANY` (categorised as a throw), and `Hyakki Gousai` likewise — flag these to the parser author but they do not hurt the number.

## Ruleset rationale

3rd Strike is the **lenient anchor** of the set — looser than `SFA3`, much looser than `HSF2`. Its input engine has negative edge, a generous shortcut for the shoryuken, skippable diagonals, and a wide buffer with a forgiving priority system, so junk inputs mid-motion are tolerated.

- `dp_double_tap = True` — 3S's signature: holding a downward direction and tapping toward twice comes out as a dragon punch. This is the one thing HSF2/SFA3/KoF do not do.
- `dp_skip_down = True` — `f,df` (no clean `d`) registers a DP in 3S.
- `lenient_diagonals = True` — the buffer reads `d,f` as a quarter circle; diagonals may be skipped.
- `charge_ms = 800` — 3S charge moves want roughly 40 frames (~670 ms); 800 is a touch conservative but defensible, I would not raise it. `charge_release_ms = 250` — generous, in keeping with the rest of the engine.
- `negative_edge = True` — 3S has negative edge (recorded for display only; the terminal can't see releases).
- `motion_window_ms = 420`, `activation_window_ms = 220`, `step_gap_ms = 210`, `max_intermediate = 2`, `tail_states = 3` — the widest windows and highest junk tolerance of the four games, reflecting the SF3 buffer.
- `mash_count = 4`, `rotation_window_ms = 600`, `rotation_slack = 3`.
- **Charge characters**: Remy and Urien fully; Alex, Chun-Li, Oro and Q each have one or two charge specials.
- **Headline quirk taught**: the auto-shoryuken (`dp_double_tap`) — the same keystrokes that give nothing in Super Turbo / Alpha 3 give a reversal here.

```python
Ruleset(
    motion_window_ms=420,
    activation_window_ms=220,
    step_gap_ms=210,
    max_intermediate=2,
    tail_states=3,
    lenient_diagonals=True,
    charge_ms=800,
    charge_release_ms=250,
    dp_double_tap=True,
    dp_skip_down=True,
    negative_edge=True,
    mash_count=4,
    rotation_window_ms=600,
    rotation_slack=3,
)
```

## Test seeds

- **ryu**: `DOWN_DOUBLE_TAP_FORWARD_HP` → `Shouryuu Ken` (the `sfa3`/`hsf2` tests of the identical script expect `[]`). `QUARTER_CIRCLE_FORWARD_HP` → `Hadou Ken`. `HALF_CIRCLE_THROUGH_DOWN_MK` → `Joudan Sokutou Geri` (`hcf + K`, a 3S-only Ryu move — `[]` in the SF2/Alpha rulesets).
- **ken-masters**: `DOWN_DOUBLE_TAP_FORWARD_HP` → `Shouryuu Ken`; `QUARTER_CIRCLE_FORWARD_HP` → `Hadou Ken`. Confirms the DP shortcut is roster-wide, not a Ryu special case.
- **chun-li**: custom — hold `DOWN` ~820 ms, then `UP` + `HK` → `Spinning Bird Kick` (`Charge d,u + K`). `QUARTER_CIRCLE_FORWARD_HP` → `[]`: her fireball (Kikou Ken) is `hcf + P`, so the script that fireballs for Ryu does nothing for her.
- **urien**: custom — hold `BACK` ~820 ms then `FORWARD` + `HK` → `Chariot Tackle`; hold `DOWN` ~820 ms then `UP` + `HP` → `Dangerous Headbutt` (`Charge d,u + P`); a ~300 ms hold → `[]`. The ~820 ms hold fires here (`charge_ms=800`) but would fail under `HSF2`'s 950 ms.
