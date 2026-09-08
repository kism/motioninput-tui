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
in `games/rulesets.py`, a parser in `datagen/<key>.py`, the generated roster
JSON, and motion tests. Do them in this order.

## Never commit or quote the guide text

`references/*.txt` and `references/*_concise.txt` are gitignored and
copyrighted by their authors. Read them, quote nothing from them into a
commit message, docstring, comment, issue or PR, and never `git add -f` one.
Only the parsed rosters under `games/data/` are committed.

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

## 3. Make the concise guide

```bash
./scripts/run-concise-guides.sh <key>
```

Run this in the background (roughly a minute per 1000 lines of guide) and read
`references/<key>_concise.txt` when it finishes — that is what you write the
ruleset and parser from, not the full guide.

## 4. Write the `GameSpec`

Add one to `src/motioninput_tui/games/rulesets.py`. Base the `Ruleset` fields
on what the concise guide's own notes say about the game's input behaviour
(dragon punch shortcuts, whether diagonals can be skipped, charge timing,
negative edge) — read the `Ruleset` docstring in `src/motioninput_tui/engine/ruleset.py`
field by field, and use `HSF2`/`SFA3`/`SFIII3` as reference points along a
strict-to-lenient range rather than guessing in a vacuum.

Set `buttons=` to the matching `ButtonSet` from `src/motioninput_tui/controls/buttons.py`
if the game is not on a Street Fighter six-button panel (`STREET_FIGHTER` is
the default).

## 5. Write the parser

Look at two existing parsers before starting:

- `src/motioninput_tui/datagen/hsf2.py` — directions spelled out in full.
- `src/motioninput_tui/datagen/sfa3.py` — shorthand (`qcf,qcf + K`) with a
  fixed-width column.

Your guide's dialect is probably close to one of these. Write
`src/motioninput_tui/datagen/<key>.py` with a `parse(text) -> tuple[list[Character], ParseReport]`,
using the helpers in `datagen/common.py` (`DASHED`, `build_move`,
`finish_character`, `split_name_command`, `character_key`) to find character
headings and move lines, and let `datagen/normalise.parse_command` turn the
command text into a `MotionSpec` — it already understands both existing
dialects' direction tokens, so a new parser rarely needs new normalisation
logic, just to get the guide's text into a form it recognises.

Register the parser in `src/motioninput_tui/datagen/__main__.py`'s `PARSERS` dict.

## 6. Fix character names if needed

If the guide's names collide with another game's for the same character, or
are just ugly (`"ken-masters"`), add an override to
`src/motioninput_tui/datagen/names.py`'s `OVERRIDES` dict, keyed by game.

## 7. Generate and inspect the roster

```bash
motioninput-tui-datagen --show-skipped
```

Expect roughly 80-90% trainable. Read the skipped list: a move skipped because
it is a genuine stance/follow-up is fine, but if a whole character's moves are
skipped the parser probably missed their heading.

## 8. Write motion tests

Make `tests/engine/test_motions/<key>/` and a `test_<character>.py` per
character covered, named and pathed after the game and character keys (see
`docs/development.md#motion-tests` for the full convention). Reuse
`tests/engine/test_motions/harness.py`'s shared canonical scripts where they
apply, so the same keys at the same moments can be shown giving a different
answer in this game than in the others.

## 9. Check everything

```bash
./scripts/run-ci-local.sh
```

Fix anything ruff, ty or pytest flag before considering the game done.
