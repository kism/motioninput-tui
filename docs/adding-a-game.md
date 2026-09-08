# Adding a game

Five pieces make up a game: a reference guide (linked, not committed), a
`GameSpec` (its `Ruleset` and button set), a parser that turns the guide's move
list into `MotionSpec`s, the generated roster JSON, and motion tests that check
specific characters against how the real game behaves.

This page is the manual walkthrough. If you would rather hand the mechanical
parts to Claude, see [Getting Claude to do it](#getting-claude-to-do-it) at the
bottom — the `add-a-game` skill follows the same steps.

## 1. Link a guide

Reference guides are fetched from GameFAQs, not committed: they are written by
their authors and may not be redistributed, so `references/*.txt` is
gitignored and every user fetches their own copy. What *is* committed is
[`sources.json`](https://github.com/kism/motioninput-tui/blob/main/src/motioninput_tui_guides/sources.json),
which records where each one came from.

Add an entry — `kof98` and `kof2001` are already there, waiting for a parser,
if you want a game with nothing else to do first:

```json
{
  "key": "kof98",
  "name": "The King of Fighters '98: The Slugfest",
  "url": "https://gamefaqs.gamespot.com/arcade/562642-the-king-of-fighters-98-the-slugfest/faqs/185",
  "credit": "Move List and Guide by Kao_Megura (Chris MacDonald)"
}
```

`key` is the short name used everywhere else (the filename stem, the `--game`
value, the test directory). `url` is the specific FAQ the parser will be
written against — GameFAQs often has several move-list FAQs for one game, and
they are not interchangeable. `credit` records which one, so a page that
changes author is caught rather than silently parsed as if nothing moved.

Then fetch it and record its checksum:

```bash
uv sync --extra guides
uv run python -m motioninput_tui_guides --game kof98
uv run python -m motioninput_tui_guides --checksums   # paste the sha256 into sources.json
```

The fetcher refuses anything under 1KB or that looks like a Cloudflare block
page, so a bad fetch fails loudly rather than writing garbage. The checksum is
what catches a *good* fetch of a page that later changed underneath you: every
run checks the guide on disk against `sha256`, freshly downloaded or not.

## 2. Read the concise version

The full FAQ runs to hundreds of kilobytes, most of it story, strategy and
combos. `references/<key>_concise.md` is a quarter the size, and standardised
Markdown: an `## heading` per character, a `| Move | Input |` table under each,
the notation key, and anything the guide says about how the game reads inputs
(diagonal leniency, dragon punch shortcuts, negative edge, charge times) under
an `## Input behaviour` heading. Move names and input text are copied verbatim;
only the layout around them is regularised. Make it if it does not exist yet:

```bash
./scripts/run-concise-guides.sh kof98
```

Read this before writing the ruleset — see the
[`concise-guides` skill](https://github.com/kism/motioninput-tui/blob/main/.claude/skills/concise-guides/SKILL.md)
for what it keeps and why. The parser in step 4 is written against the full
guide instead, since that is what datagen parses and it keeps the column layout
the concise Markdown regularised. Both the full and the concise guide are
gitignored and copyrighted: never commit one, quote one back into a commit
message, a docstring, an issue or a PR, and never `git add -f` past the ignore.

## 3. Write the `GameSpec`

Add one to
[`games/rulesets.py`](https://github.com/kism/motioninput-tui/blob/main/src/motioninput_tui/games/rulesets.py),
next to the three that are there. The
[`Ruleset` docstring](https://github.com/kism/motioninput-tui/blob/main/src/motioninput_tui/engine/ruleset.py)
documents every field; the existing three are a good starting range to
interpolate within — `HSF2` is strict, `SFA3` a little more forgiving, `SFIII3`
the lenient one. What the concise guide's own notes on input behaviour tell you
should decide where the new game sits, not a guess:

* Does a dragon punch need a genuine `f, d, df`, or does the game give a
  shortcut for holding down and tapping forward twice (`dp_double_tap`)?
* Can diagonals be skipped (`lenient_diagonals`), so `d, f` alone reads as a
  quarter circle?
* How long is a charge held (`charge_ms`), and how forgiving is the release
  window (`charge_release_ms`)?
* Does releasing a button ever complete a special (`negative_edge`)?

`buttons` on `GameSpec` names the panel — see
[`controls/buttons.py`](https://github.com/kism/motioninput-tui/blob/main/src/motioninput_tui/controls/buttons.py).
Most games use the Street Fighter six, which is the default; a game on another
panel (Mortal Kombat's five, Neo Geo's four, Tekken's four) points `buttons` at
the matching `ButtonSet` instead, or a new one if none fits.

## 4. Write the parser

The parser runs against the full `references/<key>.txt`, not the concise guide
(`datagen/__main__` reads `spec.reference`), so write it looking at the full
guide's move-list section — the concise Markdown regularised the column
alignment a fixed-width parser keys off.

Every guide spells its move list a different way, so
[`datagen/<key>.py`](https://github.com/kism/motioninput-tui/tree/main/src/motioninput_tui/datagen)
is bespoke, but the pieces are shared. Compare the two existing dialects before
writing a third:

* [`hsf2.py`](https://github.com/kism/motioninput-tui/blob/main/src/motioninput_tui/datagen/hsf2.py)
  parses a guide that spells directions out in full: `D, DF, F + any Punch`.
* [`sfa3.py`](https://github.com/kism/motioninput-tui/blob/main/src/motioninput_tui/datagen/sfa3.py)
  parses shorthand (`qcf,qcf + K`) with a fixed-width ISM column at the start
  of each line.

Both lean on
[`datagen/common.py`](https://github.com/kism/motioninput-tui/blob/main/src/motioninput_tui/datagen/common.py)
(`DASHED` for section rules, `build_move` / `finish_character` to assemble a
`Character`, `split_name_command`, `character_key`) and both hand the command
text to
[`normalise.parse_command`](https://github.com/kism/motioninput-tui/blob/main/src/motioninput_tui/datagen/normalise.py),
which reduces either dialect to a canonical list of direction tokens and looks
them up in one motion table. A new dialect almost never needs a third
normaliser — it needs a `parse()` that finds the character headings and the
move lines and gets their text into a form `parse_command` already understands.

Register it:

```python
# datagen/__main__.py
from . import hsf2, kof98, sfa3, sfiii3

PARSERS = {"hsf2": hsf2.parse, "kof98": kof98.parse, "sfa3": sfa3.parse, "sfiii3": sfiii3.parse}
```

## 5. Fix character names

Guides disagree about what a character is called across titles and authors.
[`datagen/names.py`](https://github.com/kism/motioninput-tui/blob/main/src/motioninput_tui/datagen/names.py)
maps the key a guide produced to the name to use instead, per game:

```python
OVERRIDES: dict[str, dict[str, str]] = {
    "kof98": {"kyo-kusanagi": "Kyo"},
}
```

Keys are rebuilt from the new name, so an override renames the character
everywhere — `--character`, the saved config, the test directory name. An
override that matches nobody, or that collides with another character's key,
logs a warning rather than doing nothing silently.

## 6. Generate and check the roster

```bash
motioninput-tui-datagen --show-skipped
```

This parses every game with a registered parser and writes
`games/data/<key>.json`, which **is** committed. Expect roughly 80-90% of
listed moves to become trainable; the rest are follow-ups, stances and
conditional moves ("press P during Ducking") the engine has no model of, and
they still show up in the move list struck through. `--show-skipped` lists
what did not parse — worth a scan for a new game, since a skipped move is
sometimes a parser gap rather than a genuinely unmodellable one.

## 7. Write motion tests

Motion behaviour is checked per game, per character, against the real game —
see [Development](development.md), "Testing," for the full convention. The
short version: make `tests/engine/test_motions/<key>/` and a `test_<character>.py`
per character you cover, named and pathed after the game and character keys.

```python
from tests.engine.test_motions.harness import DOWN, FORWARD, HP, press, release


def test_quarter_circle_forward_is_a_fireball(play) -> None:
    attempt = play([press(DOWN, 0), press(FORWARD, 70), release(DOWN, 110), press(HP, 150)])
    assert attempt.directions == "↓ ↘ →"
    assert attempt.moves == ["Fireball"]
```

Reuse `harness.py`'s shared canonical scripts (`DOWN_DOUBLE_TAP_FORWARD_HP` and
friends) where they apply — the point of sharing them is to show the same keys
at the same moments giving a different answer in the new game than they do in
3rd Strike or Alpha 3, which is the whole reason this trainer exists.

## 8. Run everything

```bash
./scripts/run-ci-local.sh
```

## Getting Claude to do it

Steps 1, 2, 4 and 6 are mechanical and well specified: link a page, condense
it, translate a fixed-width text format into a small parser, run a generator
and read its output. Steps 3, 5 and 7 need judgement (reading what the guide
says about the game's own feel, picking sensible defaults, writing tests that
actually distinguish this game from the others), but are still concrete enough
to hand over with a guide link and a game key.

The `add-a-game` skill walks through exactly the steps above, in order, with
the same cautions about never committing or quoting the guide text. Ask for it
by name, or just ask to add a game and name the GameFAQs page — either invokes
it. It in turn uses the `concise-guides` skill for step 2.
