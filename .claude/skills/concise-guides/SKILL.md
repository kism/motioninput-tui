---
name: concise-guides
description: Create references/<game>_concise.md for any game guide that lacks one, by running the claude CLI over references/<game>.txt to strip everything not needed to add a game to the trainer. Use before adding a new game, when a concise guide is missing, or when asked to condense or refresh the reference guides.
---

# Concise reference guides

The FAQs in `references/` run to hundreds of kilobytes each, most of it story,
strategy, combos and credits. Adding a game needs only the roster, the moves
with their inputs, the notation key and whatever the guide says about how the
game reads inputs. `references/<game>_concise.md` is that, and every game should
have one.

Reading a concise guide instead of the full one is the point: it is roughly a
quarter of the size, so it leaves room in context for the work itself.

It is standardised Markdown: an `## Character Name` per character, that
character's moves in a `| Move | Input |` table, the notation key as a table or
bullet list, and the input-behaviour notes as prose under their own heading.
Move names and input text are copied verbatim; only the surrounding layout is
regularised.

## Do not commit or quote these files

The guides are written by their authors and may not be redistributed. A
condensed version is still their work. `references/*.txt` and
`references/*_concise.md` are both gitignored, so this is only a matter of not
defeating it: never `git add -f` one, never paste its contents into a commit
message, a comment, a docstring, an issue or a pull request. Only the parsed
rosters under `games/data/` belong in the repository.

## Making the missing ones

```bash
./scripts/run-concise-guides.sh              # every guide that lacks one, then check them
./scripts/run-concise-guides.sh sfa3 kof98   # just these
./scripts/run-concise-guides.sh --force sfa3 # redo one that exists
```

That is the usual way in. It runs the two scripts below in turn, and passes its
arguments through to the first:

```bash
.claude/skills/concise-guides/make-concise-guide.sh   # condense
.venv/bin/python .claude/skills/concise-guides/verify-concise-guide.py
```

It leaves existing files alone. Running it with no arguments rebuilds every
*missing* one, which means paying for a `claude -p` pass over each full guide, so
the wrapper warns and (on a terminal) asks before doing it — you only need that
when adding a game or when a guide changed underneath its concise version. Each
guide is split into chunks of 900 lines and each chunk goes through `claude -p`,
because a whole KOF guide is too much to hand back in one reply. Expect roughly a minute per 1000 lines; the
five current guides take about a quarter of an hour, so run it in the background
and get on with something else.

Nothing is written unless every chunk succeeds and the result is a plausible
size, so a failed run leaves the previous file untouched rather than a truncated
one.

If there is no guide to condense, fetch it first:

```bash
uv run python -m motioninput_tui_guides           # all of them
uv run python -m motioninput_tui_guides --list    # what is available
```

The CLI is found via `$CLAUDE_BIN`, then `claude` on `PATH`, then the binary
bundled with the VS Code extension. `MODEL`, `CHUNK_LINES` and `REFERENCES` can
be overridden by environment variable.

## Checking the result

The wrapper above ends with this, and it can be run on its own:

```bash
.venv/bin/python .claude/skills/concise-guides/verify-concise-guide.py
```

The condensed guide is Markdown, so the check is a fuzzy one: it cannot parse
the reformatted move lists, so instead, for a game that already has a parser, it
parses the *full* guide for the characters and move names the trainer expects
and checks how many of those names still appear anywhere in the Markdown
(ignoring case, punctuation and spacing). Every character must be named and at
least 85% of move names must be findable.

```text
hsf2: 9,991 of 40,464 bytes (25%)
    characters: 17/17 found (100%)
    moves: 110/112 found (98%)
    names survived
```

`NAMES MISSING` means the condensation dropped or mangled a move list. Redo that
game with `--force`, and with a smaller `CHUNK_LINES` if it happens again. A move
name that got legitimately rephrased (a `(lowercase guess)` name spelled
differently) can drag the percentage down without anything being wrong — check
the listed misses before re-running.

A new game has no parser yet, so only the size is checked. Read the file before
trusting it: an `## heading` per character, a move table under each, every move
present.

## What the condensation keeps

The prompt lives in `make-concise-guide.sh`. It keeps character names as `##`
headings, every move as a row in that character's `| Move | Input |` table with
the move name and input copied verbatim, the notation key as a table or list,
and any statement about input timing, buffering, motion leniency, shortcuts,
negative edge or charge times under an `## Input behaviour` heading. Everything
else goes.

Only the *layout* is regularised — move names and input text are still copied
character for character, because the datagen parser you write next reads inputs
like `qcf,qcf + K` literally. That parser runs against the full guide, not this
one (`datagen/__main__` reads `spec.reference`), so when its exact column widths
matter, look at `references/<game>.txt`; the concise guide is for learning the
roster and the rules fast. If you change the prompt, re-run the verifier on
`hsf2`, `sfa3` and `sfiii3`: all three have parsers, so all three will tell you
at once whether the new prompt still preserves the names.
