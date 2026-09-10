---
game: sfa3
panel: street-fighter
closest_parser: sfa3
predicted_trainable: 55
model: Claude Sonnet 5
---
# Street Fighter Alpha 3 — brief

A three-ISM (X/A/V) Capcom arcade fighter on the standard six-button panel; its headline quirk is the ISM flag column prefixing every move line, and a combo-tree cast (Rainbow Mika, Gen, Vega) whose follow-up chains dominate the move list far more than in the other three references.

## Roster

- **28 characters total**: the 25-strong main roster from section 2 (Adon, Akuma, Birdie, Blanka, Cammy, Charlie, Chun-Li, Cody, Dan Hibiki, Dhalsim, Edmond Honda, Gen, Guy, Karin Kanzuki, Ken Masters, M. Bison, Rainbow Mika, Rolento Schugerg, Rose, Ryu, Sagat, Sakura Kasugano, Sodom, Vega, Zangief) plus the 3 genuinely-playable hidden characters in section 3 (Balrog, Juli, Juni).
- Unlike KoF '98's "Style Character" appendix, section 3 here is **not** alternate versions of already-listed characters — Balrog, Juli and Juni have their own real move lists and belong in the roster, not on a skip list.
- **Skip**: the table of contents (line ~39, `2.  CHARACTER MOVES LIST` appears here first with no dashed rules around it — this is the false-positive occurrence the parser must not use), and the huge prose sections after `4.  SECRETS AND CODES` (title colors, hidden-mode codes, boss chart, translations, endings, win poses) — none of it is move-list data.
- **Name overrides**: none needed. Every heading is already clean, English Capcom romanisation (`M. BISON` → `character_key` gives `m-bison`; `RAINBOW MIKA` → `rainbow-mika`, etc.). The one thing to note rather than fix: `RAINBOW MIKA  (Mika Nanakawa)` — the parenthetical alt-name is matched by the header regex but never captured, so her display name stays `Rainbow Mika`, which is correct and needs no override.
- **Heading form**: a dashed rule, then `NAME` (all caps, optionally `NAME  (Parenthetical)`), then a dashed rule — e.g. `-------\nADON\n-------`. No variant subtitle line like KoF's `[ bracketed subtitle ]`; the hidden characters in section 3 use the identical two-dash-rule form, which is exactly why the parser doesn't need to special-case them.

## Guide anatomy (for the parser)

- **Move-list section**: from the *second* occurrence of `2.  CHARACTER MOVES LIST` (the real section header, after the `1. HOW TO PLAY` material) to `4.  SECRETS AND CODES`. The first occurrence is the table of contents entry and must be skipped — take the last match, exactly as the existing `sfa3.py`'s `_section()` does with `starts[-1]`.
- This range **already spans both section 2 and section 3** without extra work: `3.  HIDDEN CHARACTER MOVES LIST` sits inside the window and its three character headers (`BALROG`, `JULI`, `JUNI`) match the same dashed-rule pattern as the main 25, so Balrog/Juli/Juni fall out "for free."
- **Character heading**: `^([A-Z][A-Z0-9.'\- ]{1,30})(?:\s+\([^)]*\))?$`, sandwiched between two `DASHED` rules. No captured title/team group — the parenthetical, if present, is discarded.
- **Which block to parse**: the guide's own intro says each character's list is "divided into three sections: ground and air throws, special moves and command attacks, and then Super Combos" — but all three live in one contiguous block under the heading, so unlike HSF2/KoF98 there's no short-list-vs-verbose-list choice to make. Parsing stops at `Alpha Counter (A-ISM):`, `Cancellable Attacks:`, `V-ISM Variable Attacks:`, or a `- ` prose bullet — the existing `_STOP` regex and the `line.lstrip().startswith("- ")` check.
- **Dialect**: `qcf + P` / `f,d,df + P` / `Charge b,f + P` shorthand — the same dialect Alpha 3's own parser defines and that KoF '98/2001 borrowed. `closest_parser` is therefore `sfa3` itself; there is nothing to seed from elsewhere.
- **Line-level quirk unique to this guide**: every move line is prefixed by a fixed 5-character **ISM flag column** (`XAV  `, ` AV  `, `X    `, ` A   `, `XA   `) made only of `X`, `A`, `V` and spaces, with at least one letter present. `_match_move`'s `ISM_COLUMN = 5` check strips this before `split_name_command` runs — get this column width wrong and every move line fails to parse.
- **Condition suffixes** (not prefixes, unlike KoF): `qcf + P,P when close` / `... when far`, handled by `_QUALIFIERS` (`when close|when far`). **Air prefix**: `In air, d + HP`, stripped by the literal `"in air,"` replace in `_strip_noise`. **Follow-ups**: `Tap K during Jaguar Varied Assault`, `Somersault Skull Diver — b / f + P after Head Press`, correctly caught by `_UNSUPPORTED`'s `during`/`after`.

## Notation & engine fit

- **Buttons are the native SF six** — `LP MP HP LK MK HK` — on the `STREET_FIGHTER` `ButtonSet`. No panel remap is needed here, unlike the Neo Geo games' `_neo_buttons`-style translate-then-map-back dance.
- **No token collisions**: direction tokens (`b f d u ub uf db df`) and button tokens (`lp mp hp lk mk hk p k ppp kkk pp kk`) never overlap once the command is lowercased, so there's nothing analogous to KoF's `B`/`D` vs `b`/`d` clash.
- **Motions absent from `_MOTION_TABLE` / `_CHARGE_TABLE`** (skipped as "unrecognised motion"), verified by tracing `normalise.py` against the guide text rather than guessing:
  - `b,db,d` — a down-back-then-down reversal shape distinct from the table's `(b, d, db)` (`RDP`). Hits Dhalsim's Yoga Escape, Cody's Bad Spray, and Sodom's Tengu Walking (`b,db,d + K (reversal only)`) — 3 moves.
  - `f,df,d` — Sodom's Kouten Okiagari (`f,df,d + P (reversal only)`) — 1 move, no table entry in either direction order.
  - `db,f` — Vega's V-ISM Scarlet Terror, literally `Charge db,f + K` in the guide (almost certainly meant as a plain `b,f`, but the parser must take the text as written) — 1 move, not in `_CHARGE_TABLE`.
  - Tilde-joined direction alternatives inside a charge command, e.g. `Charge d,ub~uf + P` (Vega's Sky High Claw, Kabe Hari Tsuki) and `Charge d,ub~uf + K` (Gen's Ouga): `_tokens_in` only recognises tokens from a fixed set and drops the whole `ub~uf` chunk, truncating the motion to a bare `d` and producing a skip instead of `CHARGE_DU`. ~3 moves (their `...then` follow-up siblings are already excluded by the follow-up rule regardless).
  - A single two-stage command with no recognised follow-up keyword: M. Bison's second `Somersault Skull Diver` line, `Charge d,u + P, b / f + P` — the grammar has no notion of "charge move, then a second free button," so this either mis-parses or drops out; 1 move.
- **Contrast with the other panels**: `Any direction but u / d + PP` (air throws, command throws) and `b / f + PP` (normal throws) both correctly become `MotionKind.ANY` with a 2-button requirement — SFA3's command-throw notation is far more engine-friendly than KoF's `When close, b / f + C`, which is why command throws are *not* a major loss category here the way they are for KoF98.
- **Predicted trainable ≈ 55%.** This is lower than KoF98's 63% not because of parser bugs, but because SFA3's cast leans heavily on branching follow-up trees that the guide (correctly) writes as prose ("do nothing after…", "press P during…", "move b/f, press P"): Rainbow Mika's entire Sardine's Beach Special/Dageki/Haigotori tree, Gen's Ouga/Kouga wall-bounce branches, Vega's Rolling…/Izuna Drop finishers, Cammy/Juli/Juni's Hooligan Combination branches, Guy's Hayagake sub-kicks, Rolento's Mekong Delta chain, and Cody's knife-armed move set. These are dozens of moves the engine has no concept of and is right to drop, on top of the small `_MOTION_TABLE` gaps above.

## Ruleset rationale

`sfa3` already has a shipped `Ruleset` (`src/motioninput_tui/games/rulesets.py`); the values below match what real Alpha 3 play calls for, so this section validates rather than replaces it.

- Sits **between `HSF2` and `SFIII3`**: looser buffering and a wider motion window than Super Turbo, but — critically — it still demands a genuine `f,d,df` for a dragon punch, which is a Capcom-arcade fact confirmed throughout the guide (every Shouryuu Ken/Gou Shouryuu Ken/Tiger Uppercut is written as the full three-direction motion, never as a "hold down" shortcut).
- `dp_double_tap = False`, `dp_skip_down = False` — no 3rd-Strike-style shortcut; Alpha 3's dragon punches genuinely require the diagonal.
- `lenient_diagonals = False` — the guide is precise about `d,f` (a fireball motion, `qcf`) versus `f,d,df` (a dragon punch); collapsing them would misclassify real inputs.
- `charge_ms = 880`, `charge_release_ms = 200` — Alpha 3 charge windows run close to a second in practice (roughly SF2-era, a touch shorter than HSF2's), with a slightly more forgiving release than SF2/ST.
- `negative_edge = True` — the Alpha series has negative edge, unlike Super Turbo.
- `motion_window_ms = 300`, `activation_window_ms = 150`, `step_gap_ms = 170`, `max_intermediate = 1`, `tail_states = 2` — mid-point values between the strict SF2 numbers and 3rd Strike's wider ones, consistent with Alpha 3's noticeably looser (but not SNK-loose) buffer.
- **Charge characters**: Charlie, Vega, Birdie, Blanka, Chun-Li, M. Bison, Edmond Honda, Balrog (plus Cammy's and Juni's Level-3 supers, which are charge-based even though their bread-and-butter specials are motion-based).
- **Headline quirk**: the three-way split this game sits in the middle of — no dragon-punch shortcut *and* negative edge, versus HSF2 (neither) and 3rd Strike (both). Nothing else in the roster teaches that specific combination.

```python
Ruleset(
    motion_window_ms=300,
    activation_window_ms=150,
    step_gap_ms=170,
    max_intermediate=1,
    tail_states=2,
    lenient_diagonals=False,
    charge_ms=880,
    charge_release_ms=200,
    dp_double_tap=False,
    dp_skip_down=False,
    negative_edge=True,
    mash_count=5,
    rotation_window_ms=500,
    rotation_slack=2,
)
```

## Test seeds

- **ryu**: `QUARTER_CIRCLE_FORWARD_HP` → `Hadou Ken`. `DOWN_DOUBLE_TAP_FORWARD_HP` → `[]` — no dp shortcut, same outcome as `hsf2` and unlike `sfiii3`. A clean `f,d,df + HP` script → `Shouryuu Ken`.
- **chun-li**: hold `DOWN` for `charge_ms` then `UP` + `HK` → `Tenshou Kyaku` (`Charge d,u + K`). The guide lists this move twice — once plain, once `(reversal only)` — both reduce to the same `CHARGE_DU` motion, exercising `common.py`'s `_dedupe`.
- **vega**: hold `BACK` for `charge_ms` then `FORWARD` + `LP` → `Rolling Crystal Flash` (`Charge b,f + P`, trainable). A second script following his literal `Charge d,ub~uf + P` command (Sky High Claw) should currently produce `[]` — a regression seed for the tilde-token gap flagged above, worth re-running once `_tokens_in` is taught `ub~uf`/`db~df`.
- **adon** vs **cody**: `HALF_CIRCLE_THROUGH_DOWN_MK`-shaped script ending `b,d,db` + `LK` → Adon's `Jaguar Kick` (a real `(b, d, db)` `RDP` motion). The mirror-image script `b,db,d` + `LP` against Cody should give `[]` for his Bad Spray, even though both read as "half a reverse-dragon-punch" to a human — the engine only recognises one of the two direction orderings, and this pair makes that gap visible in a test.
