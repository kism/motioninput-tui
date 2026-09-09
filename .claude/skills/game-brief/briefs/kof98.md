---
game: kof98
panel: neo-geo
closest_parser: sfa3
predicted_trainable: 63
model: Claude Sonnet 5
---
# The King of Fighters '98: The Slugfest — brief

A Neo Geo four-button team fighter; the input quirk it teaches is that SNK
buffering is generous but there is no dragon-punch shortcut, and its supers use
compound motions (`qcf,hcb`) that roll through one shared direction.

## Roster

- **41 characters** — the 38-strong main roster plus the three Real Orochi Team
  members. Main roster by team:
  - Hero: Kyo Kusanagi, Benimaru Nikaido, Goro Daimon
  - Fatal Fury: Terry Bogard, Andy Bogard, Joe Higashi
  - Art of Fighting: Ryo Sakazaki, Robert Garcia, Yuri Sakazaki
  - Ikari: Leona, Ralf Jones, Clark Steel
  - Psycho Soldier: Athena Asamiya, Sie Kensou, Chin Gentsai
  - Women's Fighting: Chizuru Kagura, King, Mai Shiranui
  - Kim: Kim Kaphwan, Choi Bounge, Chang Koehan
  - '97 Special: Ryuji Yamazaki, Blue Mary, Billy Kane
  - Orochi: Yashiro Nanakase, Shermie, Chris
  - Yagami: Iori Yagami, Mature, Vice
  - Father: Heidern, Takuma Sakazaki, Saishu Kusanagi
  - American Sports: Heavy D!, Lucky Glauber, Brian Battler
  - Edit Character: Rugal Bernstein, Shingo Yabuki
  - Real Orochi Team: Orochi Yashiro, Orochi Shermie, Orochi Chris
- **Skip** section 3's "Style Character" entries (`KYO KUSANAGI (KoF '95 Style
  Character)`, `TERRY BOGARD (Real Bout 2 Style Character)`, …, `OMEGA RUGAL`).
  They are alternate versions of characters already listed and their keys would
  collide. Detect by the team string containing `Style Character`.
- **Name overrides** (`datagen/names.py`, keyed by the key `character_key()`
  produces from the guide heading):
  - `kawa-ita-daichi-no-yashiro` → `Orochi Yashiro`
  - `arekuruu-inabikari-no-shermie` → `Orochi Shermie`
  - `honoo-no-sadame-no-chris` → `Orochi Chris`
  The main roster's `ALL-CAPS` headings title-case cleanly (`HEAVY D!` →
  `Heavy D!`) and need nothing.
- **Heading form**: `NAME␠␠…␠␠(Team)` between two dashed rules. The Real Orochi
  Team has a three-line variant with a `[ bracketed subtitle ]` between the name
  and the closing rule.

## Guide anatomy (for the parser)

- **Move-list section**: from the second occurrence of `2.  CHARACTER MOVELISTS`
  (line ~424; the first is the table of contents) to `4.  SECRETS AND TRICKS`
  (line ~7076). Do **not** stop at `3.  ALTERNATE CHARACTERS` (line ~5744) — the
  Real Orochi Team lives past it; the "Style Character" skip handles the rest.
- **Character heading**: `^\s*([A-Z][A-Z0-9.'! -]{1,40}?)\s{2,}\(([^)]*)\)\s*$`,
  with `DASHED` above and either `DASHED` or a `^\s*\[.*\]\s*$` subtitle then
  `DASHED` below.
- **Per-character source**: the fixed-width **`[ Short Moves List ]`** block —
  from the line containing that marker to the next `----[ … ]----` bracketed
  rule (`[ Normal Throws ]`). Parse this, not the verbose "Move Name: /
  Translation: / Move Command:" list lower down. Move lines are
  `Name␠␠…␠␠command`, so `split_name_command` handles them.
- **Dialect**: Alpha 3's `qcf + P` / `f,d,df + P` / `Charge d,u + P` shorthand.
  `datagen/kof98.py` is the parser; it was seeded from `sfa3.py`.
- **Line quirks**: follow-ups read `X + P from Aragami` / `Press P from Kono
  Kizu` — `normalise`'s `_UNSUPPORTED` now matches a bare `from` (excluding
  `from far` / `afar` / `distance`), so these fall out as non-trainable.
  Condition prefixes: `When close,`, `In air,`, `Within throw range,`.

## Notation & engine fit

- **Buttons `A B C D`**, panel `NEO_GEO`. A/B are light punch/kick, C/D the
  heavy pair; `P` means A or C, `K` means B or D.
- **The panel needs a parser-side remap.** The recogniser matches `Button`
  identity, not punch/kick family, and `normalise` only emits the SF six. So
  `kof98.py` translates each command to SF notation for `parse_command`
  (`A`→`LP`, `C`→`HP`, `P`→`any punch`, …) then maps the resulting
  `ButtonRequirement` back onto A/B/C/D with an explicit label — see
  `_neo_buttons`. `ALL_BUTTONS` stays the SF six.
- **Token collision**: the `B` and `D` button letters clash with the `b` and `d`
  direction tokens. The guide's casing disambiguates — directions are always
  lower case (`b,d,db`), button letters always upper (`+ D`) — so the remap
  regex is case-sensitive.
- **Compound super motions**, since added to `normalise._MOTION_TABLE`. A run
  of shorthands shares the direction its halves meet on, so these are seven
  tokens, not eight:
  - `qcb,hcf` → `d,db,b,db,d,df,f` — 13 moves (Iori Ya Sakazuki, Leona Rebel
    Spark, …)
  - `qcf,hcb` → `d,df,f,df,d,db,b` — 18 moves (every Ryuuko Ranbu, Ya Otome, …)
  - `hcb,f` → `f,df,d,db,b,f` — 9 close command grabs
- **Still not in `normalise._MOTION_TABLE` / `_CHARGE_TABLE`** (skipped):
  - `f,hcf`, `qcb,db,f` (Power Geyser), `d,d`, `db,f` — one or two each
- **Trainable 71%** (`386/547`), 63% before the compound motions landed. What
  is left is structural, none of it parser bugs:
  - **command throws** — every character has two `When close, b / f + C`
    unblockables plus often a running/close grab. The engine has no
    "direction + single button when close" throw, so `normalise` returns
    "no directional or multi-button requirement" (~73 moves).
  - genuine **follow-ups and stances** (~30 moves), correctly non-trainable.

## Ruleset rationale

Sits between `SFA3` and `SFIII3`, leaning `SFA3`, but with lenient diagonals on
because SNK games buffer a quarter circle done as `d,f` generously.

- `dp_double_tap = False`, `dp_skip_down = False` — KoF wants a real `f,d,df`;
  the "hold down, tap forward twice" shortcut is a Capcom SF3 thing.
- `lenient_diagonals = True` — SNK buffering; `d,f` reads as a quarter circle.
- `charge_ms = 850`, `charge_release_ms = 220` — the FAQ says "two seconds" but
  that is FAQ hyperbole; KoF '98 charges are ~40 frames. A touch longer and
  more forgiving on release than `SFA3`.
- `negative_edge = True` — KoF has it.
- `motion_window_ms = 320`, `activation_window_ms = 160`, `step_gap_ms = 180` —
  interpolated between `SFA3` and `SFIII3`.
- **Charge characters**: Leona, Ralf, Kim, Choi, Chang, Mai (Musasabi no Mai).
- **Headline quirk**: generous quarter-circle buffering with *no* dragon-punch
  leniency — the opposite tradeoff to 3rd Strike.

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
    rotation_window_ms=500,
    rotation_slack=2,
)
```

## Test seeds

The `harness.play_as` helper now lays the game's panel onto `HITBOX`, so
`HP` (key `o`) is the C button, `LP` (key `u`) is A, `MK` (key `k`) is B.

- **kyo-kusanagi**: `QUARTER_CIRCLE_FORWARD_HP` → `115 Shiki: Dokugami` (his
  `qcf + C`). `DOWN_DOUBLE_TAP_FORWARD_HP` → `[]` — no shortcut, same as
  `sfa3`. A clean `f,d,df + HP` script → `100 Shiki: Oniyaki`.
- **terry-bogard**: `QUARTER_CIRCLE_FORWARD_HP` → `Power Wave`.
  `DOWN_DOUBLE_TAP_FORWARD_HP` must not give `Rising Tackle` (it gives the
  `df + C` command normal `Rising Upper` instead).
- **iori-yagami**: `QUARTER_CIRCLE_FORWARD_HP` → `108 Shiki: Yami Barai`; clean
  dragon-punch script → `100 Shiki: Oniyaki`.
- **leona**: hold `DOWN` ~1s then `UP` + `HP` → `Moon Slasher`; hold `BACK` ~1s
  then `FORWARD` + `HP` → `Baltic Launcher`; a ~300ms hold → `[]`.
