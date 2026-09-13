---
game: samsh5sp
panel: neo-geo
closest_parser: kof98
predicted_trainable: 78
model: Claude Sonnet 5
---
# Samurai Shodown V Special / Samurai Spirits Zero Special — brief

A 2004 Neo Geo weapons fighter whose four-button panel is two slashes plus a kick and a dodge, not a punch/kick split: the glossary token `S` means "any slash (A / B / AB)" and every strong special or super is a two-button press (`AB`, `CD`), so there is no punch/kick family to route through the engine.

## Roster

- **28 characters**, alphabetical by first name, not team-grouped (this is not a team game): Basara Kubikiri, Charlotte Christine Corday, Enja, Gaira Kafuin, Galford D. Wyler, Gaoh Hinowanokami Kyougoku, Genjuro Kibagami, Hanzo Hattori, Haohmaru, Jubei Yagyu, Kazuki Kazama, Kusaregedo Youkai, Kyoshiro Senryo, Liu Yunfei, Mina Majikina, Mizuki Rashoujin, Nakoruru, Rasetsumaru, Rera, Rimururu, Shizumaru Hisame, Sogetsu Kazama, Suija, Tam Tam, Tokisada Shiro Amakusa, Ukyo Tachibana, Yoshitora Tokugawa, Zankuro Minazuki. The four ex-bosses (Amakusa, Mizuki, Zankuro, Gaoh) are full roster entries, per "CHANGES FROM SSZ/SS5".
- **Skip**: the `TABLE OF CONTENTS` (~line 26) and everything in section `2.  GENERAL INFORMATION` (~line 150) — the `FAQ NOTATION` glossary and the `BASIC COMMANDS` block (~line 260) are shared moves, not per-character. Skip section `4.  GAMEPLAY NOTES` (~line 2010) onward: the `MID-AIR MOVES` list re-states specials as `qcf,ub~uf + S` and would double-count, and `TRANSLATIONS` (~line 2580) is name glosses with no commands. There are **no** alternate-style character versions (nothing like KoF98's "Style Character") and no hidden-character prose to filter.
- **`datagen/names.py` overrides** (keyed by the `character_key()` of the movelist heading; cosmetic trims — `.title()` already de-shouts the ALL-CAPS headings, and no SS character collides with another game in the set, nor needs ASCII folding):
  - `charlotte-christine-corday` → `Charlotte`
  - `galford-d-wyler` → `Galford`
  - `gaira-kafuin` → `Gaira`
  - `kusaregedo-youkai` → `Kusaregedo`
  - `tokisada-shiro-amakusa` → `Amakusa`
- **Heading shape**: a lone ALL-CAPS name line between two dashed rules, e.g.
  ```
  ------------------------------------------------------------------------
  BASARA KUBIKIRI
  ------------------------------------------------------------------------
  ```
  One variant: a right-aligned parenthetical after ≥2 spaces — `GAIRA KAFUIN{spaces}("Caffeine" Gaira)` — which `sfa3._HEADER`'s optional `(?:\s+\([^)]*\))?` already strips. No subtitle lines, no team suffixes. Longest name "GAOH HINOWANOKAMI KYOUGOKU" (25 chars) fits `sfa3`'s `{1,30}`.

## Guide anatomy (for the parser)

- **Section**: from the **second** occurrence of `3.  CHARACTER MOVELISTS` (two spaces; the first is the TOC line ~40, the body header is ~line 378) to `4.  GAMEPLAY NOTES` (two spaces — the TOC writes `4. GAMEPLAY NOTES` with one space, so a substring match on `4.  GAMEPLAY NOTES` hits only the body). This is exactly `kof98._section` / `sfa3._section`: `starts[-1]`, then the first end after it.
- **Character heading**: reuse `sfa3._match_header` unchanged — `^ ?([A-Z][A-Z0-9.'\- ]{1,30})(?:\s+\([^)]*\))?$` with `DASHED` immediately above and below.
- **Block to parse**: the single fixed-width movelist that follows the heading — there is no terse/verbose split. It ends at the character's cancel chart (first line contains `Cancel chart`); also stop on a note bullet (`line.lstrip().startswith("- ")`), as `sfa3`/`sfiii3` do.
- **Column order is reversed from every existing parser.** Left = command (`qcf + S`), middle = move name, right = a one-char class flag `E` / `U` / `-` / `?` (weapon-equipped / unarmed / either / unknown). Split each line on runs of ≥2 spaces into up to three fields: `command = fields[0]`, `name = fields[1]`, discard `fields[2]`. `split_name_command` as-is mis-assigns here (it takes field 0 as the name).
- **Notation dialect**: `qcf + P` / `f,d,df + S` / `b,d,db + A` / `Charge b,f + S` shorthand — the same family `sfa3` and `kof98` use. Directions lower-case, buttons upper-case. **Closest parser: `kof98`** — start from it for the Neo Geo panel remap (`neogeo.to_neo_panel`, `neogeo.TO_SHORTHAND`, `_neo_move`, `_neo_buttons`) and the case-sensitive letter swap; take the header/section scan from `sfa3`.
- **Line-level quirks**:
  - **Follow-up lines** begin with whitespace + `_` (`  _qcf + B`, nested `    _qcf + C`); the glossary defines `_` as "Indicates follow-up command". `normalise._UNSUPPORTED` does **not** catch these (`_qcf + B` has no keyword), so the parser must `continue` on them exactly as `hsf2` does for indented continuation lines (~29 such lines across the roster).
  - **Name-column prefixes**: strip `R^ ` and `Z^ ` and mark `Category.SUPER` (`R^` = needs full Rage gauge / Rage Explosion; `Z^` = the Zetsumei Ougi). Strip `* ` (a member of a numbered move set — Yoshitora's six Tachi, Rera's Shikite; cosmetic).
  - **Condition text lives inside the command column**, not as a prefix: `qcf + S in air`, `f,d,df + C when near`, `d + S at apex of jump`, `qcb + C (hold)`, `... while dashing`, `... when hit`, `... when down`. Only `while` and `from ` (Rera's `... from * move`) are caught by `_UNSUPPORTED`. `in air` is a suffix here, so `_detect_air` (prefix/paren only) will not flag it; `when near` command throws parse as ordinary specials.
  - `(hold)`, `(air)`, `(x3)`, `(Fake)` parentheticals are handled by `_PARENTHETICAL`.

## Notation & engine fit

- **Panel `NEO_GEO`** (`ButtonSet` key `neo-geo`), buttons `A B C D`. Meanings are unique (guide "FAQ NOTATION", ~line 158): `A` weak slash, `B` medium slash, `A+B` strong slash, `C` kick, `D` dodge/special. `S` = "any Slash (A / B / AB)"; `any` = "A / B / C / D".
- **The panel needs a parser-side remap.** The recogniser matches `Button` identity, not punch/kick family, and `normalise` only emits the SF six. As in `kof98`, translate each command to SF notation for `parse_command`, then map the `ButtonRequirement` back onto `A B C D` from the original command string (`kof98._neo_move` / `neogeo.to_neo_panel`; point at `_neo_buttons`). `ALL_BUTTONS` stays the SF six.
- **`kof98`'s translation is single-letter and its `_BUTTON_LETTER = (?<![A-Za-z])([ABCDPK])(?![A-Za-z])` deliberately refuses letters with a letter neighbour** — so it silently passes over every `AB`, `AC`, `BC`, `BD`, `CD`, `ABC`, `BCD`, and there is one in almost every move list (`qcf + CD` WFT and `qcb + CD` Zetsumei are on all 28 characters). The SSV parser needs an explicit combo table applied **before** any single-letter swap — e.g. `S`→any punch, `AB`→`HP`, `C`→`LK`, `D`→`MK`, and the pairs/triples to multi-`ButtonRequirement`s.
- **Token collisions**: `B`/`b` and `D`/`d` (button vs. direction) — disambiguated by case, same as `kof98` (`b,d,db + B`). `S` and `C` have no direction twin. `n` is a genuine direction inside two motions (`f,b,d,n,u`).
- **Motions NOT in `normalise._MOTION_TABLE` / `_CHARGE_TABLE` (skipped)**:
  - **Direction ranges** — `uf~df near a wall in air` (Sankaku Tobi, on ~13 agile characters) and `a-u + C when near in air` (the diving air throws, ~5). `~` / `a-` chunks are not in `_DIRECTION_TOKENS`, so no motion is produced. **~18 moves.**
  - `hcb,f` = `f,df,d,db,b,f` — Haohmaru Zankousen, Yoshitora Yuchouka. **~2.**
  - `db,qcf` = `db,d,df,f` — Suija Shougetsu, Ukyo Tsubame Gaeshi. **~2.**
  - `d,d` — Gaira Jishin Gan, Hanzo Shizune. **~2.**
  - `b,db,d` (down-back before down; not the `b,d,db` RDP key) — Nakoruru Annu Mutsube. **~1.**
  - Written-out reversals/grabs: `f,b,f,b,f,b,d + AC/BC when hit` (Galford, Hanzo — 4); `f,b,d,n,u + C`, `f,uf,u,ub,b,db,d,n,u + CD`, `df,hcb,b,d,db + BC` (Kusaregedo — 3); `df,qcb,f,d,df + BC` (Nakoruru — 1); `b,uf,u,uf,f + AB` (Gaira — 1). **~9.**
  - `Hold any for 1.5 / 3.5 / 6.5 / 20.5 sec.` and `Hold any, release when hit` (Shizumaru) — `_SECONDS` only matches integer `for N sec`, so the seconds text is not even stripped, and there is no timed-hold model. **~5.**
  - `Charge b,f` **is** `("b","f")` → `CHARGE_BF`, so Mina's two charge moves are fine; nothing charge-related is lost.
- **Predicted trainable ≈ 78%.** It clears KoF98's 63% for one structural reason: every WFT and Zetsumei Ougi is a plain `qcf + CD` / `qcb + CD` — one quarter circle plus two buttons — so all ~56 supers are trainable and SSV has none of KoF98's compound `qcf,hcb` super motions. What keeps it under ~85%: the direction-range air moves (~18), the unmodeled command-throw and reversal motions above (~16), Shizumaru's timed charges (~5), and `... while dashing` variants that `_UNSUPPORTED` drops (~6). The figure is soft by a few points depending on whether `MotionKind.HOLD` air normals (`d + C in air`) and `f + tap S rapidly` (→ HOLD + mash) count as trainable in your build; a raw tally with those counted lands near 82%.

## Ruleset rationale

On input feel SSV Special sits next to `KOF98`, between `SFA3` and `SFIII3`: **more forgiving than `HSF2`/`SFA3` on diagonals** because SNK buffering turns `d,f` into a quarter circle (the "STORED INPUT" note ~line 2340 and the "MID-AIR MOVES … very lax timing" note describe exactly this), but with **no dragon-punch shortcut** — `f,d,df + S` means `f,d,df + S`, and holding down then tapping forward gives nothing; the double-tap DP is a 3rd Strike behaviour only. It is a deliberate, slow-walking game, but nothing in the guide says its input *read* is looser than KoF's, so the timing windows track `KOF98` rather than widening.

- `dp_double_tap = False` — SNK; a real `f,d,df` is required.
- `dp_skip_down = False` — `f,df` alone is nothing.
- `lenient_diagonals = True` — SNK buffering; `d,f` → quarter circle. Same call as `KOF98`/`KOF2001`.
- `charge_ms = 900`, `charge_release_ms = 200` — only Mina charges; the glossary's "hold … for 2 seconds" is FAQ hyperbole. Real SS charge is roughly 40–50 frames but I am not certain of the SSV value, so this mirrors `HSF2`/`KOF98` rather than asserting one.
- `negative_edge = True` — matches the SNK siblings `KOF98`/`KOF2001`; the guide does not explicitly confirm it (unlike the SFA3 FAQ), and it is display-only since the terminal cannot see releases.
- `motion_window_ms = 320`, `activation_window_ms = 160`, `step_gap_ms = 180`, `max_intermediate = 1`, `tail_states = 2` — copied from `KOF98`; no evidence to deviate.
- `mash_count = 5`, `rotation_window_ms = 500`, `rotation_slack = 2` — defaults; the only rotation-ish content is Gaira's `_spin 360 rapidly` follow-up, which is skipped.

**Charge characters: Mina Majikina only.**

**Headline quirk this game teaches**: the panel is slashes + kick + dodge, not a punch/kick split — `S` = "any slash" and the strong specials/supers are two-button presses, so `ButtonRequirement.count == 2` is the *common* case and the button mapping has no punch/kick meaning behind it.

> **Corrected when the game was added.** The brief said here that `HITBOX`
> exposes only three attack keys per row, so `D` had no key and `+ CD` moves
> could not be driven from a motion test. That is wrong: `HITBOX.attack_rows`
> is four wide (`u i o p` / `j k l ;`) and `D` is `p`. The claim came from a
> stale comment in `harness.py` naming only three, which now names four and
> adds `NEO_A`..`NEO_D`. Genjuro's `qcf + CD` is covered by a passing test.

```python
Ruleset(
    motion_window_ms=320,
    activation_window_ms=160,
    step_gap_ms=180,
    max_intermediate=1,
    tail_states=2,
    lenient_diagonals=True,
    charge_ms=900,
    charge_release_ms=200,
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

`harness.play_as` lays `NEO_GEO` onto `HITBOX`: key `u` = A, `i` = B, `o` = C, `p` = D (and `j`/`k`/`l`/`;` the same again). So in the shared scripts `HP` presses **C**, `LP` presses **A**, `MK` presses **B**. The harness exports these as `NEO_A`..`NEO_D`, which is what a test on this panel should use.

- **haohmaru** (the shoto): `DOWN_DOUBLE_TAP_FORWARD_HP` → `[]` — no DP shortcut, where 3rd Strike gives one. A clean `f,d,df` + `o` custom script → `Ougi Kogetsu Zan` (`f,d,df + S`; `S` admits C). `QUARTER_CIRCLE_FORWARD_HP` presses C, which matches both `qcf + S` (Senpuu Retsu Zan) and `qcf + C` (its Fake) — pin down which your recogniser prefers; the point is that `o` is C here, not a heavy punch.
- **mina-majikina** (only charge character): custom — hold `BACK` ~950 ms, then `FORWARD` + `o` → `Tenkyuu Shin` (`Charge b,f + C`); hold `BACK` ~950 ms then `FORWARD` + `u` → `Jikyuu Shin` (`Charge b,f + S`); a ~300 ms back hold then `FORWARD` + button → `[]`.
- **kazuki-kazama** (dense `qcf`/`f,d,df` + A/B/C/AB): `QUARTER_CIRCLE_FORWARD_HP` → `Shounetsu Kon: Saien Futatsu` (`qcf + C`); clean `f,d,df` + `o` → `Dai Bakusatsu: Saien Futatsu`; `DOWN_DOUBLE_TAP_FORWARD_HP` → `[]`.
- **galford-d-wyler** (half circles + two-button): custom half-circle-back then `u`+`o` together → `Replica Attack: Head` (`hcb + AC`); `QUARTER_CIRCLE_FORWARD_HP` → `Plasma Blade` (`qcf + S`). Exercises `HCB` plus a `count == 2` `ButtonRequirement` on the Neo panel — the combo path `kof98` never built.
