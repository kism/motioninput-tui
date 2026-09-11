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

Add an entry (the existing six are worked examples of the shape):

```json
{
  "key": "kof98",
  "name": "The King of Fighters '98",
  "url": "https://gamefaqs.gamespot.com/ps/562861-the-king-of-fighters-98/faqs/52561",
  "credit": "FAQ/Movelist by Ice Queen Zero (Andrea Castillo)"
}
```

`key` is the short name used everywhere else (the filename stem, the guide
fetcher's `--game` value, the test directory). `url` is the specific FAQ the parser will be
written against — GameFAQs often has several move-list FAQs for one game, and
they are not interchangeable. `credit` records which one, so a page that
changes author is caught rather than silently parsed as if nothing moved.

Then fetch it and record its checksum:

```bash
uv sync --group guides
uv run python -m motioninput_tui_guides --game kof98
uv run python -m motioninput_tui_guides --checksums   # paste the sha256 into sources.json
```

The fetcher refuses anything under 1KB or that looks like a Cloudflare block
page, so a bad fetch fails loudly rather than writing garbage. The checksum is
what catches a *good* fetch of a page that later changed underneath you: every
run checks the guide on disk against `sha256`, freshly downloaded or not.

## 2. Read the brief

The full FAQ runs to hundreds of kilobytes, most of it story, strategy and
combos, and reading it does not by itself tell you where the game sits on the
strict-to-lenient axis or which of its motions the engine cannot model. The
*brief* does: `.claude/skills/game-brief/briefs/<key>.md` is an analysis of one
guide against this codebase — the roster and which sections to skip, the guide's
layout so the parser can find the move list, the button and motion gotchas with
a predicted trainable rate, a proposed `Ruleset`, and motion-test seeds. Make it
if it does not exist yet:

```bash
./scripts/2-game-briefs.sh kof98
```

That is a single `claude -p` pass over the full guide, so run it in the
background. Read the brief before writing the ruleset and parser, and
read it *critically* — it is one model's homework and it can be wrong. See the
[`game-brief` skill](https://github.com/kism/motioninput-tui/blob/main/.claude/skills/game-brief/SKILL.md)
for its structure and how it is verified.

Briefs *are* committed: they are our notes — character names and the occasional
example input, never a whole move list. The guide itself
(`references/<key>.txt`) is gitignored and copyrighted: never commit it, quote
it into a commit message, a docstring, an issue or a PR, or `git add -f` past
the ignore. The parser in step 4 is written against that full guide, since that
is what datagen parses and it keeps the fixed-width columns a parser keys off.

## 3. Write the `GameSpec`

Add one to
[`games/rulesets.py`](https://github.com/kism/motioninput-tui/blob/main/src/motioninput_tui/games/rulesets.py),
next to the ones that are there. The
[`Ruleset` docstring](https://github.com/kism/motioninput-tui/blob/main/src/motioninput_tui/engine/ruleset.py)
documents every field; the Street Fighter three span a good starting range to
interpolate within — `HSF2` is strict, `SFA3` a little more forgiving, `SFIII3`
the lenient one. Start from the brief's proposed `Ruleset(...)` and its
reasoning about where the game sits, then sanity-check the fields that matter:

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
the matching `ButtonSet` instead, or a new one if none fits. A non-SF panel also
needs the parser to remap button requirements, because the recogniser matches
`Button` identity, not punch/kick family — see
[`datagen/parsers/kof98.py`](https://github.com/kism/motioninput-tui/blob/main/src/motioninput_tui_datagen/parsers/kof98.py)
and step 4.

## 4. Write the parser

The parser runs against the full `references/<key>.txt` (`datagen/__main__`
reads `spec.reference`), so write it looking at the guide's move-list section.
The brief's "Guide anatomy" section names the section markers, the
character-heading shape, which block to parse per character, and the closest
existing parser to start from.

Every guide spells its move list a different way, so
[`datagen/parsers/<key>.py`](https://github.com/kism/motioninput-tui/tree/main/src/motioninput_tui_datagen/parsers)
is bespoke, but the pieces are shared. Compare the existing dialects first:

* [`hsf2.py`](https://github.com/kism/motioninput-tui/blob/main/src/motioninput_tui_datagen/parsers/hsf2.py)
  parses a guide that spells directions out in full: `D, DF, F + any Punch`.
* [`sfa3.py`](https://github.com/kism/motioninput-tui/blob/main/src/motioninput_tui_datagen/parsers/sfa3.py)
  parses shorthand (`qcf,qcf + K`) with a fixed-width ISM column at the start
  of each line.
* [`kof98.py`](https://github.com/kism/motioninput-tui/blob/main/src/motioninput_tui_datagen/parsers/kof98.py)
  parses a guide on a non-Street-Fighter panel: `neogeo.py` translates
  `A/B/C/D` to SF notation for `normalise`, then maps the button requirement
  back onto the real panel. Copy this when the brief says the panel needs a
  remap; `kof2001.py` reads the same dialect and shares those helpers.

Both lean on
[`datagen/common.py`](https://github.com/kism/motioninput-tui/blob/main/src/motioninput_tui_datagen/common.py)
(`DASHED` for section rules, `build_move` / `finish_character` to assemble a
`Character`, `split_name_command`, `character_key`) and both hand the command
text to
[`normalise.parse_command`](https://github.com/kism/motioninput-tui/blob/main/src/motioninput_tui_datagen/normalise.py),
which reduces either dialect to a canonical list of direction tokens and looks
them up in one motion table. A new dialect almost never needs a third
normaliser — it needs a `parse()` that finds the character headings and the
move lines and gets their text into a form `parse_command` already understands.

Register it:

```python
# datagen/parsers/__init__.py  — add the new module here
from . import hsf2, kof98, kof2001, sfa3, sfiii3, ssvsp

__all__ = ["hsf2", "kof98", "kof2001", "sfa3", "sfiii3", "ssvsp"]

# datagen/__main__.py  — and register it in the PARSERS mapping
PARSERS = {
    "hsf2": hsf2.parse,
    "sfa3": sfa3.parse,
    "sfiii3": sfiii3.parse,
    "kof98": kof98.parse,
    "kof2001": kof2001.parse,
    "ssvsp": ssvsp.parse,
}
```

## 5. Fix character names

Guides disagree about what a character is called across titles and authors.
[`datagen/names.py`](https://github.com/kism/motioninput-tui/blob/main/src/motioninput_tui_datagen/names.py)
maps the key a guide produced to the name to use instead, per game:

```python
OVERRIDES: dict[str, dict[str, str]] = {
    "kof98": {"kyo-kusanagi": "Kyo"},
}
```

Keys are rebuilt from the new name, so an override renames the character
everywhere — the saved config, the test directory name. An
override that matches nobody, or that collides with another character's key,
logs a warning rather than doing nothing silently.

### Fixing a command the guide has wrong

[`datagen/commands.py`](https://github.com/kism/motioninput-tui/blob/main/src/motioninput_tui_datagen/commands.py)
is the same mechanism for a move whose *input* the guide gets wrong, keyed by
the character and move name the roster ends up with:

```python
OVERRIDES: dict[str, dict[tuple[str, str], str]] = {
    "sfa3": {("sakura", "Midare-zakura"): "qcf,qcf + K"},
}
```

Only for errors checked against the real game. A command the parser cannot model
is a different problem: that belongs in `normalise`'s tables, or stays
untrainable and struck through in the move list. A correction that matches no
move, or that does not itself parse, logs a warning and leaves the guide's
version alone.

These are the hardest problems in the roster to notice, because nothing looks
broken — the guide's command parses, the move appears, and it comes out when you
press it. It is just not the move the game has. Say in a comment what you checked
it against.

## 6. Generate and check the roster

```bash
python -m motioninput_tui_datagen --show-skipped
```

This parses every game with a registered parser and writes
`games/data/<key>.json`, which **is** committed. Compare the trainable rate to
the brief's prediction. The Street Fighter games land around 80-90%; a game can
be lower for structural reasons the brief should have called out — command
throws the engine has no model for, compound super motions absent from
`normalise`'s tables (KoF '98 is 75% for both reasons). The rest are follow-ups,
stances and conditional moves the engine cannot model, shown struck through.
`--show-skipped` lists what did not parse — scan it: a whole character missing
is a parser gap, not an unmodellable move.

`python -m motioninput_tui_datagen --summary` prints the roster on disk
character by character (move count, trainable count, category mix), which is the
quickest way to see what a regeneration changed and to spot a character whose
count looks wrong.

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

Start from the brief's "Test seeds". Reuse `harness.py`'s shared canonical
scripts (`DOWN_DOUBLE_TAP_FORWARD_HP` and friends) where they apply — the point
of sharing them is to show the same keys at the same moments giving a different
answer in the new game than they do in 3rd Strike or Alpha 3, which is the whole
reason this trainer exists. `harness.play_as` lays the game's panel onto the
layout, so `HP`/`LP`/… address whatever that panel puts in those positions.

## 8. Run everything

```bash
./scripts/run-ci-local.sh
```

## Getting Claude to do it

Steps 1, 2, 4 and 6 are mechanical and well specified: link a page, brief it,
translate a fixed-width text format into a small parser, run a generator and
read its output. Steps 3, 5 and 7 need judgement (deciding where the game sits
on the strict-to-lenient axis, picking sensible defaults, writing tests that
actually distinguish this game from the others), but the brief does most of
that homework — Claude's job is to check it and turn it into code.

The `add-a-game` skill walks through exactly the steps above, in order, with
the same cautions about never committing or quoting the guide text. Ask for it
by name, or just ask to add a game and name the GameFAQs page — either invokes
it. It in turn uses the `game-brief` skill for step 2.
