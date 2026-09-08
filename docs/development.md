# Development

Architecture and the check/test setup. For adding a new game specifically, see
[Adding a game](adding-a-game.md); for using the trainer, see [Home](index.md).

## Layout

```text
src/motioninput_tui/
  config.py      Last used selection, saved under ~/.config/motioninput-tui/.
  gamepad_probe.py  `python -m ...gamepad_probe`: dumps a pad's SDL state to /tmp.
  engine/        Device independent: notation, input buffer, motion matchers,
                 rulesets, the recogniser and a training session.
  controls/      Control layouts, button sets and input sources: keyboard,
                 plus a gamepad (optional `gamepad` extra) polled from the
                 training tick.
  games/         Game metadata, rulesets, move models and the packaged rosters.
  notation_styles.py  How a move's input is *written* (glyphs, letters, emoji);
                 separate from engine/notation.py, which is what a direction *is*.
  settings.py    The player's own preferences, layered on top of a game's rules.
  terminal/      Terminal identification, latency warnings, kitty keyboard protocol.
  tui/           Textual screens, widgets, and the release-aware input driver.

src/motioninput_tui_guides/   Fetches the FAQs from GameFAQs. A sibling package,
                              not a subpackage, so it is not shipped in the wheel.
src/motioninput_tui_datagen/  Parses the FAQs into games/data/*.json. Also a
                              sibling package, kept out of the wheel; run it with
                              `python -m motioninput_tui_datagen` (or
                              `--summary` for a per-character breakdown of the
                              data on disk). Per-game parsers live in `parsers/`.
```

Dependencies point one way: `engine` ← `controls` ← `games` ← `tui`. The engine
never touches the clock or the terminal; callers pass timestamps in, which
keeps the matchers straightforward to reason about and to test. The recogniser
takes moves through a `RecognisableMove` protocol rather than importing
`games`, which is what keeps that direction clean.

Three kinds of tuning constant sit in adjacent modules and are easy to confuse:

* `engine/ruleset.py` and `games/rulesets.py` hold **game** behaviour: motion
  windows, `step_gap_ms`, charge times, whether diagonals may be skipped,
  `dp_double_tap`. Per game.
* `controls/layouts.py` `HoldTiming` holds **device** behaviour. It has nothing
  to do with which game is selected.
* `settings.py` holds the **player's** own choices, layered on top of whichever
  game is selected — `lenient_half_circles` lives on `Ruleset` because that is
  what the matchers read, but its value comes from the player, not the game.

`decay_ms` bridges the two input models: how long the device takes to reveal
that a direction was released. Zero when the terminal reports releases,
`tap_ms` when holds are inferred. It is threaded from the session through the
recogniser into `MatchContext`, where it widens motion windows and step gaps.
Without it, inferred holds would make every motion look too slow to land.

## Screens and layouts

The screens run input picker → setup → trainer, with two modals over them:
`ctrl+b` for settings and `ctrl+n` for move notation, both opened by an action
on the app (`app.settings`, `app.notation`) so any screen can offer them and
the app — which owns the config — is the one that saves what comes back.
Escape steps back one screen; each screen dismisses and the app pushes the
next, so the stack never grows.

A `ControlLayout` is *where* the attacks are: `attack_rows`, two rows of key
codes. A `ButtonSet` (`controls/buttons.py`) is what those positions *mean*,
also as rows, and `with_buttons` lays one onto the other position by position —
a game with a different panel is a table entry, not a new layout per keyboard
arrangement. `Button` holds every game's buttons, but `ALL_BUTTONS` is still
only the Street Fighter six: it is what a *roster* can ask for, and the
generated data is Street Fighter, so widening it would change what "any
button" means in the move lists.

The first game in the list, `display`, has no roster: it is built with its
characters standing in for the button sets, which is how a panel gets picked
with the same two lists as everything else. It runs a real `TrainingSession`
(so SOCD cleaning and hold inference behave exactly as in the trainer) and
draws the panel instead of recognising anything.

## The release-aware driver

Textual asks the terminal for the kitty keyboard protocol but not for event
types, and its parser raises on the `modifiers:event-type` field, so key
releases never reach an application.
[`tui/keyboard_driver.py`](https://github.com/kism/motioninput-tui/blob/main/src/motioninput_tui/tui/keyboard_driver.py)
supplies a driver that asks for event types and understands the replies.

It reaches into Textual internals in two places: the escape sequence written in
`start_application_mode`, and the parser class the input thread builds. Both are
guarded and fall back to inferred holds. Textual is pinned; check this file
after a Textual upgrade.

`direction_from_axes` resolves simultaneous left+right by newest-wins rather
than neutral. That is a correctness requirement rather than a style choice: the
terminal cannot see the player release back as they press forward, so both are
held at once during ordinary motions, and neutral SOCD makes charge moves
impossible.

## Reference guides

`references/*.txt` are move list guides written by their authors and are **not
redistributable**, so they are gitignored and each user fetches their own copy
of pages they could equally read in a browser.
`motioninput_tui_guides/sources.json` records the exact GameFAQs page behind
each one, and the SHA-256 of the guide the parsers were written against.

```bash
uv sync --extra guides                          # curl-cffi and beautifulsoup4
uv run -m motioninput_tui_guides                # fetch anything missing
uv run -m motioninput_tui_guides --list         # catalogue, sizes, checksum state
uv run -m motioninput_tui_guides --checksums    # SHA-256 of each guide on disk
uv run -m motioninput_tui_guides --game sfa3 --force
```

The fetcher checks every guide, freshly downloaded or already on disk, against
the `sha256` in `sources.json`: a mismatch is a failure, so a changed upstream
page or a corrupt copy is caught before the parsers run. When a guide really
has changed and the new text is correct, update the checksum from
`--checksums` output and commit `sources.json`.

The scraper is a **sibling package under `src/`, not a subpackage of
`motioninput_tui`**. `uv_build` packages only the module named after the
project, so the scraper is absent from both the wheel and the sdist while
staying importable in a development checkout, where the editable install puts
all of `src/` on the path. That is also why it has no console script: an entry
point would resolve to a module that a published wheel does not contain.

Its dependencies live in the `guides` extra so the trainer never depends on an
HTTP stack. GameFAQs sits behind Cloudflare, which is why curl-cffi
(browser-like TLS) is preferred over plain requests. The scraper imports
`motioninput_tui.utils.logger`; that one-way dependency is fine for a repo tool
but means it is not independently installable.

Guides already on disk are never re-fetched, so a normal run makes no requests.
A response under 1KB, or one that looks like an anti-bot page, is treated as a
failure and nothing is written, so a block page can never masquerade as a
reference file.

You do not need the guides to run or develop the trainer; the parsed rosters are
committed. They are only needed to regenerate that data — see
[Adding a game](adding-a-game.md) for the full procedure, including the
per-game briefs that analyse each guide against the engine.

## Check/Test

```bash
./scripts/run-ci-local.sh   # ty + ruff + pytest, what CI runs
./scripts/run-coverage.sh   # coverage run + html + report
```

### Checking

Run `ruff check` or get the VS Code ruff extension; the rules are defined in
`pyproject.toml`.

Ruff runs with `select = ["ALL"]` and `preview = true`, so lint is strict.
Suppressions in this repo use `# ruff: ignore[rule-name] - why` and
`# ty: ignore[rule-name]` rather than `# noqa`, which the preview
`noqa-comments` rule enforces.

### Type checking

Run `ty`.

### Testing

Run `pytest`; it gets its config from `pyproject.toml`.

```bash
pytest tests/test__meta.py::test_repo_url          # a single test
pytest -k logger                                   # by name
pytest tests/engine/test_motions/sfiii3            # one game
pytest tests/engine/test_motions/sfiii3/test_elena.py   # one character
```

### Motion tests

Motion behaviour is checked per game and per character, because that is how it
gets validated: against the real game, one character at a time.

```text
tests/engine/test_motions/
  harness.py       Key names, script builders, the player, canonical inputs.
  conftest.py      The play fixture, bound to the file's game and character.
  test__meta_hierarchy.py  Guards the layout below.
  sfiii3/test_elena.py   3rd Strike, Elena.
  sfiii3/test_ryu.py     3rd Strike, Ryu.
  sfa3/test_ryu.py       Alpha 3, Ryu, same scripts and different answers.
```

The directory is the game key and the file name is the character key, with
underscores for the hyphens in the rosters (`test_chun_li.py` is `chun-li`).
The `play` fixture reads both out of the path, so a test never names them and
cannot be run against the wrong character. `test__meta_hierarchy.py` fails if a
directory is not a game or a file is not one of its characters.

Scripts are timestamped by hand rather than run against a real clock, and they
go in at the key level, so SOCD cleaning and the direction states it produces
are covered as well as the matchers. `attempt.directions` is the input strip as
arrows, which is what makes a failure readable. Inputs meant to be compared
across games live in `harness.py` so that every game is demonstrably being
given the same keys at the same moments.

Play defaults to `exact_input=True`, which is the terminal reporting key
releases. A test for the inferred path has to pass `exact_input=False` and
simulate the operating system's auto-repeat stream itself (first repeat after
the initial delay, then roughly every 33ms); bare presses without repeats do
not reproduce what a real terminal sends and give misleading results.

See [Adding a game](adding-a-game.md), "Write motion tests," for the concrete
recipe when covering a new game.

### Workflows

The `.github` folder has both a Check and Test workflow.

To get the workflow passing badges on your repo, see
<https://docs.github.com/en/actions/monitoring-and-troubleshooting-workflows/adding-a-workflow-status-badge>.

Or, if you are not using GitHub, check your Git hosting service's own workflow
badges, or use <https://shields.io/>, which covers most of them.

### Test coverage

#### Locally

To get code coverage locally, the config is in `pyproject.toml`, or run with
`pytest`:

```bash
python -m http.server -b 127.0.0.1 8000 -d htmlcov
```

Open the link in your browser and browse into the `htmlcov` directory.

#### Codecov

The template repo uses Codecov to get a badge on the README; see their guides
for configuring that, since it is stripped out of this repo.

## Documentation

This site is built with [Sphinx](https://www.sphinx-doc.org/) from the pages
under `docs/`, using [MyST](https://myst-parser.readthedocs.io/) so the pages
are plain Markdown rather than reStructuredText. Configuration is
`docs/conf.py`; hosting is Read the Docs, which reads `.readthedocs.yaml` at
the repository root. Build it locally with:

```bash
uv sync --extra docs
uv run sphinx-build -b html docs docs/_build/html
```

Then open `docs/_build/html/index.html`. Pass `-W` to fail the build on any
warning (an unresolved cross-reference, a heading anchor that moved) — that is
what Read the Docs itself does not enforce but is worth checking after
restructuring a page.
