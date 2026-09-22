---
game: tekken3
panel: tekken
closest_parser: hsf2
predicted_trainable: 28
model: Claude Sonnet 5
---
# Tekken 3 — brief

A 3D string/poke fighter with almost no quarter-circle, dragon-punch or charge vocabulary at all; its guide writes `<command> — <name>` (command *first*), uses `lp/rp/lk/rk` for **left**/**right** punch/kick rather than light/medium/heavy, and encodes most of its "specials" as either a single held diagonal plus a button or a comma/`~`-joined button string, which is a poor match for the SF-shaped motion tables this engine ships with.

*(Line numbers below are estimated from the guide's structure, not counted against a numbered file — re-check with `grep -n` before wiring up the real start/end markers.)*

## Roster

- **20 character headers, 19 with a usable move list.** No team grouping — the guide lists them in roughly alphabetical (by given name, except "Forest Law" filed under L) order: Bryan Fury, Dr. Boskonovich (PSX only), Eddy Gordo / Tiger, Gon (PSX only), Gun Jack, Heihachi Mishima, Hwoarang, Jin Kazama, Julia Chang, King, Kuma / Panda, Forest Law, Lei Wulong, Mokujin, Nina Williams / Anna Williams, Ogre I, Ogre II, Paul Phoenix, Ling Xiaoyu, Yoshimitsu.
- **Skip Mokujin.** His section is pure prose ("Mokujin randomly imitates one character per round…") with no move lines at all, so `finish_character` will naturally drop him (empty `moves`) — nothing special to code, just don't be surprised when he isn't in the output.
- **Three headers name two characters sharing one moveset**: `Eddy Gordo / Tiger`, `Kuma / Panda`, `Nina Williams / Anna Williams` — costume/skin swaps with an identical command list, the same shape as an "alternate version of a character already listed" in the other guides' skip lists. Recommend the header regex capture only the text before ` / ` and drop the second name, the same call `kof98.py` makes for its EX/95'/Omega alternates — duplicating the section under two keys would be pure churn since every `Move`/`command` pair would be identical.
- **Ogre I and Ogre II are distinct rosters**, not an alt-costume pair — their move lists genuinely differ (Ogre II adds the tail attacks, drops a few of Ogre I's finishers) — keep both.
- **Skip everything before the first character and after the last one**: the `*Notation*`, `*General Maneuvers*`, `*Tekken 3 Basics…*`, `*Arcade/Playstation Secrets and Tricks*` and `*What's New*` sections all sit before `*Bryan Fury*` and are universal engine mechanics, not a character's moves; `*Throw & Reversal Counters*`, `*Tekken 3 Strategy*` and `*Winning Stances*` sit after `*Yoshimitsu*` and are prose/cross-reference tables, not move lists.
- **Name overrides (`datagen/names.py`)**: none needed for spelling — `character_key()` folds names like `Dr. Boskonovich` cleanly. The only naming decision is the "take the name before ` / `" rule above, which belongs in the header regex, not `names.py`.
- **Heading form**: `*Name*` on its own line, sandwiched by a dashed rule above and a blank line below (`----…`, blank, `*Bryan Fury*`, blank, moves…). Two variants: a trailing aside outside the asterisks (`*Dr. Boskonovich* - PSX Version Only`), and the slash-paired names described above. Unlike every other parser in this trainer, there is **no** dashed rule immediately after the name — moves start right after the blank line, so the header match can't reuse `sfa3`/`sfiii3`'s "sandwiched by two `DASHED` lines" pattern.

## Guide anatomy (for the parser)

- **Move-list section**: starts at the line containing `*Bryan Fury*` (~line 205, after the front matter, notation legend, general maneuvers and secrets sections) and ends at the line containing `*Throw & Reversal Counters*` (~line 2400, after Yoshimitsu's `+Profile+` block). Both estimated — confirm with `grep -n`.
- **Character heading**: `^\*([^*]{1,40}?)\*(?:\s*-\s*.+)?\s*$`, preceded by a `DASHED` line. Stop collecting a character's moves at a line matching `^\+(Obtaining|Special Notation|Profile|Juggles)\+` or the next heading.
- **Per-character source, and the guide's one big structural inversion**: every move line is `<command>␠␠…␠␠-␠<name>`, **command before name**, the opposite of every other parser here (`hsf2`, `sfa3`, `sfiii3`, `kof98` all write `Name … command`). `common.split_name_command` assumes name-first and cannot be reused directly — write a small `^(\S.*?)\s{2,}-\s+(\S.*)$` match and pass the two groups to `build_move` in swapped order. This is the single most important guide-specific fact for whoever writes the parser.
- **Which block to parse**: the flat move list right under the character name, down to `+Juggles+` (a "which moves combo into which" appendix, not inputs) and `+Profile+` (bio/flavor). Some characters interleave named sub-stances (`-Grounded Position-`, `-Handstand Position-`, `-Snake Stance-`, …) as bare `-Label-` lines inside the move list — these don't match the two-space-before-dash move regex, so collection continues past them without special-casing, but the moves listed underneath silently lose the "only from this stance" gating (see below).
- **Dialect**: not `qcf + P` shorthand and not HSF2's spelled-out `D, DF, F`. Directions are single lowercase letters for a *tap* (`f b u d`, plus `df/db/uf/ub`) and the **same letters uppercase for a held direction** (`F B U D`) — a tap/hold distinction none of the other four guides make. Everything gets lowercased by `parse_command`, so this distinction is invisible to the engine; that's an acceptable loss since the trainer doesn't model "walk" inputs anyway. `n` (neutral) is written explicitly and often, which matters a lot (see below).
- **Line-level quirks**:
  - **`^` prefix = chain continuation** ("links after the preceding move", per the guide's own key), used constantly and nested up to five levels deep for combo/throw trees (King's multipart throw diagram is the extreme case). None of `_UNSUPPORTED`'s banned words ("during", "after", "then", …) match a bare `^`, so these lines currently parse as ordinary, unconditional commands. Recommend treating any command that starts with `^` (after stripping leading whitespace) as non-trainable outright — building the actual chain graph (`follows`) would need to track indentation depth against the correct ancestor, which given the five-level trees is more scope than this guide's payoff justifies.
  - **Parenthetical condition prefixes** — `(WS)`, `(ss left)`, `(ss right)`, `(from behind)`, `(from the left/right)`, `(while down)`, `(while back is turned)`, `(on opponent's countering rk)` — sit at the *front* of the command, e.g. `(WS)rp - Gutpunch`. `normalise._UNSUPPORTED` checks the text with parentheticals already stripped, so these are currently invisible and the move is accepted as if unconditional. Recommend a Tekken-specific pre-filter (checked before `_PARENTHETICAL.sub`) that rejects these the way `_UNSUPPORTED` rejects "when close,"/"blocking" elsewhere.
  - Trailing parenthetical annotations on the **name** side (`(NJ)`, `(HJ)`, `(BJ)`, `(BL)`, `(!)`, `(*)`, `(*C)`, `(*B)`, per-character ones like `(FB)`/`(SFB)`) are pure flavour on the move name, not the command — harmless, no action needed.

## Notation & engine fit

- **Panel**: `lp rp lk rk` — left punch, right punch, left kick, right kick. The engine already has this exact layout as `TEKKEN` (`buttons.py`): `rows=((SQUARE, TRIANGLE), (CROSS, CIRCLE))`. Use `panel: tekken`.
- **`lp`/`lk` are a false-friend collision, `rp`/`rk` are simply invisible.** `normalise._BUTTON_TOKEN` only recognises `lp mp hp lk mk hk ppp kkk pp kk p k`. Tekken's own `lp`/`lk` tokens *happen* to match that regex — but as Street Fighter's *light punch*/*light kick*, not "left punch"/"left kick", which is a different button on a different panel. `rp`/`rk` don't match the regex at all, so a command like `lp+rp` currently loses its `rp` half silently: `_BUTTON_TOKEN.findall("lp+rp")` finds only `lp`, and the two-button throw comes back as a single-button requirement rather than failing loudly. This is exactly the problem `kof98.py`'s `_neo_buttons` was built to solve for the Neo Geo panel: translate the guide's own vocabulary to the SF six for `parse_command`, then map the resulting `ButtonRequirement` back onto the real panel. Recommend the same shape here: `lp→"lp"`, `rp→"mp"`, `lk→"lk"`, `rk→"mk"` (reusing SF's medium slot as a stand-in for "right"), then remap `LP→SQUARE, MP→TRIANGLE, LK→CROSS, MK→CIRCLE` afterwards. Do this translation *before* calling `parse_command`, not after, since the button-family logic (`_named_requirement`, `_button_chain`) needs both halves of a `+`/`,` pair to be recognisable tokens simultaneously.
- **`~` (immediate follow-up)** is used for tight natural-combo links (`rp~lp`, `lk~rk`) as distinct from the comma-joined strings (`lp,rp`). Untranslated, `_BUTTON_TOKEN.findall` on `rp~lp` (post-remap) finds both tokens and — because there's no comma — `_button_chain` never sees them as a sequence, so `_parse_buttons` folds them into a single *simultaneous* two-button requirement. That's not a rejection, it's a wrong answer: the trainer would teach "press both at once" for a move that's really "press one, then the other." Recommend normalising `~` to `,` as a pre-processing step before `parse_command`, the same class of fix as `kof98.py`'s `to_shorthand`.
- **Token collisions between directions and buttons**: none beyond the `lp`/`lk` case above — `rp`/`rk` don't collide with anything in `_DIRECTION_TOKENS`, and the diagonals (`df db uf ub`) are already exactly what `_WORD_DIRECTIONS`/`_HOLD_DIRECTIONS` expect, so no translation is needed there.
- **Almost nothing here is in `normalise._MOTION_TABLE`.** Tekken's directional vocabulary is built around an explicit return to neutral (`n`), which the SF-derived table has no concept of at all:
  - `("f","n","d","df")` — the "crouch dash" shape behind most characters' signature mid-hitting special (Heihachi/Jin's Wind Godfist, Hwoarang's stance-entry, King's grapple starters, Julia's `D,df` openers). Not a key in the table under any spelling. Roughly 20–30 moves guide-wide use this exact shape.
  - `("f","f")` / `("b","b")` / `("f","f","f")` — the dash-in/dash-back-into-attack shape (`f,f+rp`, `b,b+rk`, `f,f,F+rp`…). Extremely common — every character has several. This single missing shape probably costs 150+ moves across the roster, more than any other single gap.
  - A handful of genuine SF-shaped motions *do* exist and *will* match once buttons are translated: Yoshimitsu's `d,df,f+lp` (QCF), Eddy's `b,db,d,df,f+lp+rp` (HCF), a couple of Nina/King grapple throws built the same way. Small in number but worth confirming as a positive test case.
  - Near-miss variants with an extra leading/trailing token (King's `f,b,db,d,df,f+lp` Giant Swing, Kuma's `f,df,d,db,b,f+lp+rp` Circus Roll) fall just outside the existing HCF/HCB keys — not worth adding bespoke six/seven-token entries for one move each.
  - The one real rotation notation, `B,360degCnterC` / `f,360degClkwse`, coincidentally *does* get picked up: `normalise._parse_rotation` only checks `"360" in text`, and `"360degcnterc"` contains that substring, so it resolves to `MotionKind.ROTATE_360` almost by accident. Worth a regression test precisely because it's accidental.
- **What actually is trainable**: a single held diagonal plus a button (`df+lp` → `MotionKind.HOLD`, genuinely correct here — Tekken crouch pokes really do require holding the diagonal at the moment of the press) and two-button-no-direction presses (`lp+lk` → `MotionKind.ANY`, correct for the basic throws/taunts) both fall out of the *existing* fallback paths in `_resolve_directions`/`_without_directions` with no new table entries needed. Comma-joined button strings (`lp,rp`, tenstrings) are exactly what `MotionKind.SEQUENCE` was built for and, once the button remap is wired up, should parse cleanly for the majority of the guide's "combo string" entries — this is genuinely the best-aligned part of the whole guide.
- **28% trainable is a low-confidence estimate**, driven by:
  - the `f,f`/`b,b`/`f,n,d,df` gaps above (structural, guide-wide, not fixable by better regexes — the motion table itself has no concept of a required neutral);
  - `^`-prefixed chain continuations, recommended non-trainable above, which are a large fraction of every character's list (deep combo/throw trees);
  - stance-prefixed moves (`(WS)`, `-Grounded Position-` sub-blocks, …), recommended non-trainable once the pre-filter above is added — until it is, these will parse as if unconditional, which would make the true "correctly trainable" number *lower* than whatever `--show-skipped` reports.

## Ruleset rationale

There's essentially no decompiled or well-documented frame data for Tekken 3's input reader to hand, and — more importantly — almost none of the `Ruleset` fields describe anything this guide's move set actually uses: no dragon punch shape exists (`dp_double_tap`/`dp_skip_down` are inert), no charge characters exist (`charge_ms`/`charge_release_ms` are inert, like Martial Masters), and negative edge isn't a documented Tekken mechanic. The fields that *do* matter are `sequence_window_ms` (the strings) and, if a future engineer builds out the `^` chain graph, `chain_window_ms`.

- `lenient_diagonals = False` — the guide spells every diagonal out explicitly (`df`, `db`, never a bare `d,f`); no decompilation to check against, so this stays off by the same reasoning as Sailor Moon and Martial Masters.
- `dp_double_tap = False`, `dp_skip_down = False` — no dragon-punch-shaped motion exists in this roster at all.
- `charge_ms = 900`, `charge_release_ms = 200` — inert defaults; no charge characters.
- `negative_edge = False` — not a Tekken mechanic.
- `motion_window_ms/activation_window_ms/step_gap_ms/max_intermediate/tail_states` — left at SFA3-adjacent interpolated defaults; almost nothing in this roster exercises them, since so little matches `_MOTION_TABLE` at all.
- `sequence_window_ms = 2000` — reckoned, not measured. SFA3/USFIV/SFIII3 use 1200ms for a five-to-six-press run (a target combo, Akuma's Raging Demon); Tekken's tenstrings are twice as long, so the window is scaled up proportionally rather than guessed from nothing. Flag this clearly as a guess in the ruleset's own comment, the way `sailormoons.py`/`martmast.py` flag theirs.
- `chain_window_ms = 0` — left inert. Recommended default *unless* a future engineer implements the `^` chain graph, at which point 700ms (the trainer's usual reckoned figure for a landed-parent follow-up) would be the natural starting point.
- **Charge characters**: none.
- **Headline quirk this game teaches that the others don't**: there is no motion vocabulary at all in the SF sense — a "special move" here is either a held diagonal plus a button, or a scripted run of plain button presses, and the guide's own punctuation (`,` vs `~` vs `^`) is doing work (sequence vs. tight-link vs. chain-gated) that none of the other five games' dialects need to express.

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
    chain_window_ms=0,
    sequence_window_ms=2000,
)
```

## Test seeds

The shared `harness.py` canonical scripts all press `HP` (key `o`), which is **not bound on the Tekken panel at all** — `TEKKEN`'s rows only supply two buttons per row (`SQUARE,TRIANGLE` / `CROSS,CIRCLE`), the same "runs out early" situation `SNES_FIGHTER` hits, so `o`/`p`/`l`/`;` are dead on this game. Recommend adding `TEKKEN_LP, TEKKEN_RP = "u", "i"` and `TEKKEN_LK, TEKKEN_RK = "j", "k"` aliases to `harness.py` before writing any Tekken tests; none of `QUARTER_CIRCLE_FORWARD_HP`, `DOWN_DOUBLE_TAP_FORWARD_HP` or the half-circle scripts are relevant here anyway, since none of their shapes exist in `_MOTION_TABLE`'s Tekken-relevant subset.

- **heihachi-mishima**: hold `DOWN` then add `FORWARD` (down-forward), then press `TEKKEN_LP` → `Uppercut` (`df+lp`, a plain `MotionKind.HOLD`). A companion script of two quick `FORWARD` taps then `TEKKEN_RP` should come back `[]` — `Rushing Uppercut (NJ)`'s `f,f+rp` is the `("f","f")` shape the motion table doesn't have, a good regression anchor for that gap.
- **paul-phoenix**: `TEKKEN_LP` tap, release, `TEKKEN_RP` tap within the sequence window → `One-Two` (`lp,rp`, a two-step `MotionKind.SEQUENCE`) — the best available positive test for the button-remap-then-sequence pipeline.
- **king**: `TEKKEN_RP` + `TEKKEN_RK` pressed together → `Suplex` (`rp+rk`, `MotionKind.ANY`). This one specifically exercises the `rp`/`rk` half of the remap that `lp`/`lk` alone can't catch — before the remap is wired up, `rp+rk` finds no button tokens at all and fails outright (a clean rejection), whereas an `lp`-involving command like `lp+rp` would fail *silently wrong* instead. Worth having both kinds of case in the suite.
- **bryan-fury**: `TEKKEN_LP` + `TEKKEN_LK` together → `DDT` (`lp+lk`), then — if the `^`-prefix pre-filter is implemented — a bare `TEKKEN_LP`+`TEKKEN_RP` press with no preceding `Run` should **not** produce `Flying Cross Chop` (`^lp+rp`, chain-gated on `f,f,f - Run` actually landing), confirming chain-gated moves aren't reachable standalone.
