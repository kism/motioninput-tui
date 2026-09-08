---
name: add-a-game
description: Add a new game to the trainer end to end - link its reference guide, write its Ruleset and button set, write a parser for its move list, generate the roster, and write motion tests. Use when asked to add a game, a new title, a new character roster, or given a GameFAQs move-list link to turn into a trainer entry.
---

# Adding a game

The full explanation of every step below lives in
[`docs/adding-a-game.md`](../../../docs/adding-a-game.md) — read it if
anything here is unclear, it has the reasoning this skill only summarises.
This skill is the checklist for doing it.

A game is five pieces: a linked (not committed) reference guide, a `GameSpec`
in `games/rulesets.py`, a parser in `motioninput_tui_datagen/parsers/<key>.py`, the generated roster
JSON, and motion tests. Do them in this order.

## Never commit or quote the guide text

`references/*.txt` is gitignored and copyrighted by its authors. Read it,
quote nothing from it into a commit message, docstring, comment, issue or PR,
and never `git add -f` one. Only the parsed rosters under `games/data/` and
the analysis in `.claude/skills/game-brief/briefs/` (character names and the
odd example input, never whole move lists) are committed.

## 1. Find or confirm the guide link

Check `src/motioninput_tui_guides/sources.json` first — `kof98` and
`kof2001` are already linked with no parser, so if asked for one of those the
guide link is already done.

Otherwise you need a specific GameFAQs move-list FAQ URL for the game (ask the
user if they have not given one). Add an entry:

```json
{
  "key": "<key>",
  "name": "<full game name>",
  "url": "<GameFAQs FAQ URL>",
  "credit": "<FAQ title/author, from the page>"
}
```

`key` becomes the filename stem, the `--game` value and the test directory
name — pick something short and stable.

## 2. Fetch it and record the checksum

```bash
uv sync --extra guides
uv run python -m motioninput_tui_guides --game <key>
uv run python -m motioninput_tui_guides --checksums
```

Paste the printed sha256 into the new `sources.json` entry. If the fetch fails
(too small, or looks like a Cloudflare interstitial), the URL is probably wrong
or the page needs a different one — do not force a bad guide through.

## 3. Read the game brief

```bash
./scripts/run-game-briefs.sh <key>
```

If the brief already exists (it is committed), just read it. Otherwise run this
in the background and read
`.claude/skills/game-brief/briefs/<key>.md` when it finishes. It is analysis,
not a copy of the guide: the roster and which sections to skip, the guide's
layout for the parser, the button/motion gotchas and a predicted trainable
rate, a proposed `Ruleset`, and motion-test seeds. Steps 4-8 below are the
brief's homework turned into code — read it critically, it can be wrong.

## 4. Write the `GameSpec`

Add one to `src/motioninput_tui/games/rulesets.py`, starting from the brief's
proposed `Ruleset(...)` call. Sanity-check it against the `Ruleset` docstring in
`src/motioninput_tui/engine/ruleset.py` field by field, and against
`HSF2`/`SFA3`/`SFIII3` as strict-to-lenient reference points.

Set `buttons=` to the `ButtonSet` the brief names (from
`src/motioninput_tui/controls/buttons.py`) if the game is not on the Street
Fighter six-button panel (`STREET_FIGHTER`, the default). A non-SF panel also
needs the parser to remap button requirements — see step 5 and
`datagen/parsers/kof98.py`.

## 5. Write the parser

Work from the full `references/<key>.txt`. The brief's "Guide anatomy" section
names the move-list section markers, the character-heading shape, which block to
parse per character, and the closest existing parser to start from:

- `src/motioninput_tui_datagen/parsers/hsf2.py` — directions spelled out in full.
- `src/motioninput_tui_datagen/parsers/sfa3.py` — shorthand (`qcf,qcf + K`) with a
  fixed-width column.
- `src/motioninput_tui_datagen/parsers/kof98.py` — shorthand on a non-SF panel: it
  translates `A/B/C/D` to SF notation for `normalise`, then maps the button
  requirement back onto the real panel (`_neo_buttons`). Copy this when the
  brief's "Notation & engine fit" section says the panel needs a remap.

Write `src/motioninput_tui_datagen/parsers/<key>.py` with a
`parse(text) -> tuple[list[Character], ParseReport]`, using the helpers in
`datagen/common.py` (`DASHED`, `build_move`, `finish_character`,
`split_name_command`, `character_key`), and let `datagen/normalise.parse_command`
turn the command text into a `MotionSpec`. A new parser rarely needs new
normalisation logic — but the brief flags any motions this guide uses that are
not in `normalise`'s tables, and those stay non-trainable unless you extend the
engine.

Register the parser: import it in `src/motioninput_tui_datagen/parsers/__init__.py`
(and its `__all__`), then add it to the `PARSERS` dict in
`src/motioninput_tui_datagen/__main__.py`.

## 6. Fix character names if needed

Add the `datagen/names.py` `OVERRIDES` entries the brief's "Roster" section
lists (names that collide with another game, or are just ugly like
`"ken-masters"`), keyed by game.

## 7. Generate and inspect the roster

```bash
python -m motioninput_tui_datagen --show-skipped
```

Compare the trainable rate to the brief's prediction. Read the skipped list: a
move skipped because it is a genuine stance/follow-up, a throw the engine has no
model for, or a motion the brief flagged as unsupported is expected; a whole
character skipped means the parser missed their heading.

## 8. Write motion tests

Start from the brief's "Test seeds". Make `tests/engine/test_motions/<key>/` and
a `test_<character>.py` per character covered, named and pathed after the game
and character keys (see `docs/development.md#motion-tests`). Reuse
`tests/engine/test_motions/harness.py`'s shared canonical scripts where they
apply, so the same keys at the same moments can be shown giving a different
answer in this game than in the others. `harness.play_as` lays the game's panel
onto the layout, so `HP`/`LP`/… address whatever the panel puts there.

## 9. Check everything

```bash
./scripts/run-ci-local.sh
```

Fix anything ruff, ty or pytest flag before considering the game done.
