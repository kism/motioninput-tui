# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Textual TUI for practising fighting game motion inputs. You pick a game and a
character, press inputs, and it shows which move the game would have given you.
The whole point is that the same input differs per game: in 3rd Strike holding
down and double tapping forward gives a dragon punch, in Alpha 3 and Super
Turbo it gives nothing.

See `README.md` for using the trainer and `README_DEV.md` for the developer
setup; this file covers what is hard to discover from the code alone.

## Commands

```bash
uv sync --all-extras            # dev setup; omit --all-extras for prod

.venv/bin/ruff format .         # format
.venv/bin/ruff check --fix .    # lint
.venv/bin/ty check .            # type check
.venv/bin/pytest -q             # tests
./scripts/run-ci-local.sh       # ty + ruff + pytest, what CI runs
./scripts/run-coverage.sh       # coverage run + html + report
./scripts/run-concise-guides.sh # condense any guide lacking references/<game>_concise.txt

.venv/bin/pytest tests/test__meta.py::test_repo_url        # a single test
.venv/bin/pytest -k logger                                 # by name
.venv/bin/pytest tests/engine/test_motions/sfiii3          # one game's motion tests

python -m motioninput_tui                                  # run it
python -m motioninput_tui --game sfiii3 --character ryu    # skip the pickers
python -m motioninput_tui --check-terminal                 # speed + key release support
python -m motioninput_tui --list                           # rosters
python -m motioninput_tui.datagen --show-skipped           # rebuild packaged rosters
python -m motioninput_tui_guides --list                    # reference guide catalogue
```

When adding a game, read `references/<game>_concise.txt` rather than the full
guide: same roster, move lists, notation key and input-behaviour notes, about a
quarter of the size. The `concise-guides` skill makes any that are missing and
verifies them by parsing both files and comparing rosters. They are derived from
the guides, so they are gitignored and must not be committed or quoted either.

`src/motioninput_tui_guides/` fetches `references/*.txt` from GameFAQs. It is a
sibling package rather than a subpackage so `uv_build` leaves it out of the
wheel; keep it that way, and do not give it a console script. Its dependencies
live in the `guides` extra (`uv sync --extra guides`). The fetched guides are
copyrighted, gitignored, and must never be committed or quoted back into the
repo; only the parsed rosters under `games/data/` are.

Ruff runs with `select = ["ALL"]` and `preview = true`, so lint is strict.
Suppressions in this repo use `# ruff: ignore[rule-name] - why` and
`# ty: ignore[rule-name]`, not `# noqa`; the preview `noqa-comments` rule
enforces that.

## Config

`config.py` remembers the last game, character, layout and buffer policy in
`~/.config/motioninput-tui/config.json` (honouring `XDG_CONFIG_HOME`). It is
best-effort throughout: a missing, corrupt or unwritable file logs and falls
back to defaults rather than raising. `Config` doubles as the app's starting
selection and its persistence, which is why `MotionInputApp` takes one instead
of separate game/character/layout arguments.

Key release support is deliberately not persisted; it is probed per terminal
each launch.

Setting `OptionList.highlighted` queues a highlight event, and an OptionList
also posts one for index 0 when options are added. `SetupScreen` therefore
applies the remembered selection from `call_after_refresh`, not `on_mount`, or
the queued events overwrite it. Focus is set there too, since the character
list has no options until then.

## Architecture

Dependencies point one way: `engine` ← `controls` ← `games` ← `tui`.

**`engine/` is device and terminal agnostic and never reads a clock.** Callers
pass `at_ms` timestamps in. `engine/recognizer.py` takes moves through a
`RecognisableMove` Protocol rather than importing `games`, which is what keeps
that direction clean. Preserve this: it is why the matchers can be driven
deterministically.

Reading order for the interesting parts: `engine/notation.py` (numpad
directions, player on the left, so 6 is forward) → `engine/buffer.py` →
`engine/motions.py` → `engine/ruleset.py` → `engine/recognizer.py` →
`engine/session.py`.

### Two input models

Terminals report key presses and auto-repeats but **not releases**. The trainer
handles this two ways and the distinction runs through several files:

* **Exact.** Terminals speaking the kitty keyboard protocol do report releases.
  `terminal/kitty.py` holds the protocol; `tui/keyboard_driver.py` supplies a
  Textual driver that asks for event types and emits `KeyRelease`. `__main__`
  probes with `query_support()` *before* Textual takes the terminal, so holds
  are exact from the first keystroke.
* **Inferred.** Otherwise `controls/layouts.py` deduces holds from auto-repeat.
  `HoldTiming` documents the reasoning. A press counts as held for `tap_ms`; a
  burst of fast repeats proves a genuine hold; the OS repeat delay is measured
  as you play and `tap_ms` widens to match.

`decay_ms` is the bridge between them: how long the device takes to reveal a
release. Zero when exact, `tap_ms` when inferred. It is threaded
session → recogniser → `MatchContext` → matchers, where it widens motion
windows and step gaps. Without it, inferred holds would make every motion look
too slow to land.

### Two kinds of tuning constant, easily confused

* `engine/ruleset.py` / `games/rulesets.py` — **game** behaviour. Motion
  windows, whether diagonals can be skipped, charge times, `dp_double_tap`
  (the headline SF3 difference). Per game.
* `controls/layouts.py` `HoldTiming` — **device** behaviour. Nothing to do with
  which game is selected.

### Spending inputs

Games flush the command buffer when a special activates. Two mechanisms
enforce this together, and both are needed:

* `InputBuffer.consume()` on activation (normals and throws do not flush,
  matching the games).
* `Ruleset.step_gap_ms` bounds the pause between consecutive steps of a motion.
  A total-span limit is not enough on its own: the forward you are still
  holding after a fireball survives the flush, and without a per-step limit a
  later `d, df` would turn it into a dragon punch.

`BufferPolicy.LOOSE` (`--loose-buffer`, `ctrl+b`) disables both.

### SOCD is last-input priority, deliberately

`direction_from_axes` resolves simultaneous left+right by newest-wins rather
than neutral. This is a correctness requirement, not a style choice: the
terminal cannot see you release back as you press forward, so both are held at
once during ordinary motions. Neutral SOCD makes charge moves impossible.

### Rosters are generated and committed

`games/data/*.json` is produced from the guides in `references/` by `datagen/`.
Those guides are gitignored, so a fresh clone has to run
`python -m motioninput_tui_guides` first. After changing `datagen/normalise.py` or a
parser, rerun `python -m motioninput_tui.datagen` and commit the JSON. Roughly 80-90% of
listed moves become trainable; the rest are follow-ups and conditional moves
that still appear in the move list, struck through.

The guides disagree about character names, so `datagen/names.py` maps the key a
guide produced to the name to use instead, per game (`ken-masters` → `Ken`).
Keys are rebuilt from the new name, so an override renames the character
everywhere, including `--character` and anyone's saved config — which is why
`__main__` forgets a remembered character that is no longer in the roster
instead of refusing to start.

## Fragile coupling

`tui/keyboard_driver.py` reaches into Textual internals in two places: the
escape sequence in `start_application_mode`, and swapping the parser class the
input thread builds. Both are guarded and fall back to inferred holds. Textual
is pinned; check this file after a Textual upgrade.

## Testing

`tests/engine/test_motions/` is one directory per game and one file per
character (`sfiii3/test_chun_li.py`), because that is how the behaviour is
validated: against the real game, a character at a time. The directory is the
game key and the file name is the character key with underscores for hyphens.
The `play` fixture in its `conftest.py` reads both out of the path, so tests
never name a game or a character; `test_hierarchy.py` fails on a directory that
is not a game or a file that is not one of its characters. Add a game by making
the directory.

`harness.py` holds the key names, the `press`/`release` script builders, the
player itself, and the inputs that are deliberately shared between games so the
same keys at the same moments can be shown to give a dragon punch in 3rd Strike
and nothing in Alpha 3. Scripts carry explicit timestamps rather than running
against a real clock, and go in at the key level, so SOCD cleaning is covered
too. Assert on `attempt.directions` (the strip as arrows) and `attempt.moves`.

Play defaults to `exact_input=True`. For the inferred path a test must pass
`exact_input=False` and also simulate the OS auto-repeat stream (first repeat
after the initial delay, then ~33ms apart) — bare presses without repeats do
not reproduce how a real terminal behaves and will give misleading results.
