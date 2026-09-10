---
name: prepare-release
description: Check the documentation and the app's own on-screen text before a numbered release - that nothing names a renamed identifier or a removed flag, that quoted figures still match the rosters, that docs have not regrown a copy of something a menu already draws, and that the in-app notes and setting details are still true. Use when preparing or cutting a release, bumping the version, or asked to check the docs and in-app text.
---

# Preparing a release: documentation and in-app text

The app is the documentation. Every screen has a `Footer` listing its keys, the
setup pane and the `ctrl+b` modal print each setting's name, state and
`Setting.detail`, the `ctrl+n` menu draws every notation style as its own
preview, and the pickers list the games with `GameSpec.notes[0]` under them.

Two things follow, and they are what this check is for. The app's own strings
are user-facing prose and go stale like any other; and anything in `docs/` that
repeats them is a second copy that will disagree with the first. See *Writing
documentation* in `CLAUDE.md` for the rule this enforces.

Release also means the manual play-testing register in
[`docs/manual-testing.md`](../../../docs/manual-testing.md). That is a person's
job, not this skill's — but check the register still lists the right characters
if the roster changed.

## 1. Run the checker

```bash
.venv/bin/python .claude/skills/prepare-release/check-docs.py
```

`FAIL` is wrong and blocks the release. `LOOK` is a smell that is often fine —
read it, decide, move on. It exits non-zero only on failures, so it can go in a
release script.

It checks what a machine can be sure of:

- every repository path a doc names exists
- every backticked identifier is still in the source (this is what catches a
  rename — `_load_pygame` outliving `load_pygame`)
- every flag in a documented **command** exists on the entry point that command
  runs, checked per entry point because the guide fetcher has a `--game` and
  the trainer does not. Prose may still name a removed flag; that is how
  `CLAUDE.md` explains the removal
- every trainable percentage matches the rosters on disk, ranges bracketing a
  real one
- every playable game has notes, no note counts the roster ("strictest of the
  three" was true at three games), every setting has a name and a detail, and
  every `Binding` has a description or is explicitly hidden
- docs are not re-listing the settings, the notation styles, or a run of
  `ctrl+` keys

Add to the allow-lists at the top of the script rather than loosening a check:
`IGNORED_PATHS`, `NOT_OUR_CODE`, `THIRD_PARTY_FLAGS`.

## 2. Regenerate and diff the rosters

```bash
.venv/bin/python -m motioninput_tui_datagen
git diff --stat src/motioninput_tui/games/data/
```

Should be empty. If it is not, the committed data was stale — commit it, then
re-run the checker, because every figure quoted in the docs comes from it.

## 3. Read the app's own text

The checker catches empty and stale-by-pattern, not wrong. Read these as a
player would:

```bash
.venv/bin/python -c "
from motioninput_tui.games.rulesets import GAME_SPECS
for k, s in GAME_SPECS.items():
    if not s.reference: continue
    print(k); [print('   ', n) for n in s.notes]"
```

- `notes[0]` is what the picker shows under the highlighted game, so it has to
  say what makes *that* game different in one line.
- Every note has to be true of the current ruleset. A note claiming a shortcut
  or a window that has since been retuned is the worst kind of wrong: it reads
  as authoritative.
- `Setting.detail` is the only explanation a player gets of a setting. Check it
  against what the setting now does.

## 4. Judge the docs

Only a person can do this part. For each section of `docs/index.md`, ask
whether the app already says it — and if it does, delete it rather than keeping
the two in sync.

Keep what the app cannot show:

- why a game's rules differ, and where the figures come from
- what the config file remembers and where it lives
- gotchas the interface has no room for — the Neo Geo `D` being unreachable on
  a keyboard is the standing example
- anything to be fixed outside the program: key repeat rates, terminal choice

Delete on sight: a table of settings, a table of notation glyphs, a list of key
bindings, a picture of a screen, a table of games and their keys.

## 5. Build and test

```bash
./scripts/run-ci-local.sh
uv run sphinx-build -b html docs docs/_build/html   # needs: uv sync --group docs
```

Sphinx must build with no warnings, and a new page must be in the `toctree` at
the bottom of `docs/index.md` or it is unreachable.

## 6. README

`README.md` is not built by Sphinx, so nothing above validates its links. Check
by hand that the Read the Docs links resolve, and that its short game list and
install commands still match `docs/index.md`.
