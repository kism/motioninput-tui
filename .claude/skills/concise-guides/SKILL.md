---
name: concise-guides
description: Create references/<game>_concise.txt for any game guide that lacks one, by running the claude CLI over references/<game>.txt to strip everything not needed to add a game to the trainer. Use before adding a new game, when a concise guide is missing, or when asked to condense or refresh the reference guides.
---

# Concise reference guides

The FAQs in `references/` run to hundreds of kilobytes each, most of it story,
strategy, combos and credits. Adding a game needs only the roster, the moves
with their inputs, the notation key and whatever the guide says about how the
game reads inputs. `references/<game>_concise.txt` is that, and every game
should have one.

Reading a concise guide instead of the full one is the point: it is roughly a
quarter of the size, so it leaves room in context for the work itself.

## Do not commit or quote these files

The guides are written by their authors and may not be redistributed. A
condensed version is still their work. `references/*.txt` is gitignored, which
already covers `*_concise.txt`, so this is only a matter of not defeating it:
never `git add -f` one, never paste its contents into a commit message, a
comment, a docstring, an issue or a pull request. Only the parsed rosters under
`games/data/` belong in the repository.

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

It leaves existing files alone, so running it with no arguments is the normal
way to satisfy "every game should have one". Each guide is split into chunks of
900 lines and each chunk goes through `claude -p`, because a whole KOF guide is
too much to hand back in one reply. Expect roughly a minute per 1000 lines; the
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

For a game that already has a parser this is a real check rather than a
formality: it runs the parser over both files and compares the rosters. Getting
the same characters and the same move counts out of the condensed guide means
the move lists survived intact.

```text
hsf2: 9,991 of 40,464 bytes (25%), same roster
    full:    17 characters, 112 moves, 94 trainable (84%)
    concise: 17 characters, 112 moves, 94 trainable (84%)
```

`ROSTER DIFFERS` means the condensation dropped or mangled a move list. Redo
that game with `--force`, and with a smaller `CHUNK_LINES` if it happens again.

A new game has no parser yet, so only the size is checked. Look at the file
before trusting it: character headings should still be there, and move lines
should have their original column alignment, because a parser will be written
against that exact layout.

## What the condensation keeps

The prompt lives in `make-concise-guide.sh`. It keeps character names and their
headings, move lines copied out character for character with their original
spacing, the notation key, and any statement about input timing, buffering,
motion leniency, shortcuts, negative edge or charge times. Everything else goes.

The instruction not to reformat matters more than it looks. The parsers in
`datagen/` read fixed-width `Name    command` lines and hunt for heading shapes,
so a guide rewritten into tidy markdown tables would be worse than useless for
writing one. If you change the prompt, re-run the verifier on `hsf2`, `sfa3` and
`sfiii3`: all three have parsers, so all three will tell you at once whether the
new prompt still preserves what matters.
