# motioninput_tui development

Architecture, the character data pipeline, and the check/test setup. For
installing and using the trainer, see [README.md](README.md).

## Layout

```text
src/motioninput_tui/
  engine/        Device independent: notation, input buffer, motion matchers,
                 rulesets, the recogniser and a training session.
  controls/      Control layouts and input sources. Keyboards today, gamepads later.
  games/         Game metadata, rulesets, move models and the packaged rosters.
  datagen/       Parsers that turn the reference FAQs into games/data/*.json.
  guides/        Fetches those FAQs from GameFAQs. Optional deps, not imported
                 by the trainer.
  terminal/      Terminal identification, latency warnings, kitty keyboard protocol.
  tui/           Textual screens, widgets, and the release-aware input driver.
```

Dependencies point one way: `engine` <- `controls` <- `games` <- `tui`. The
engine never touches the clock or the terminal; callers pass timestamps in,
which keeps the matchers straightforward to reason about and to test. The
recogniser takes moves through a `RecognisableMove` protocol rather than
importing `games`, which is what keeps that direction clean.

Two kinds of tuning constant sit in adjacent packages and are easy to confuse:

- `engine/ruleset.py` and `games/rulesets.py` hold **game** behaviour: motion
  windows, `step_gap_ms`, charge times, whether diagonals may be skipped,
  `dp_double_tap`. Per game.
- `controls/layouts.py` `HoldTiming` holds **device** behaviour. It has nothing
  to do with which game is selected.

`decay_ms` bridges the two input models: how long the device takes to reveal
that a direction was released. Zero when the terminal reports releases,
`tap_ms` when holds are inferred. It is threaded from the session through the
recogniser into `MatchContext`, where it widens motion windows and step gaps.
Without it, inferred holds would make every motion look too slow to land.

## The release-aware driver

Textual asks the terminal for the kitty keyboard protocol but not for event
types, and its parser raises on the `modifiers:event-type` field, so key
releases never reach an application.
[`tui/keyboard_driver.py`](src/motioninput_tui/tui/keyboard_driver.py) supplies
a driver that asks for event types and understands the replies.

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
of pages they could equally read in a browser. `guides/sources.json` records the
exact GameFAQs page behind each one.

```bash
uv sync --extra guides       # curl-cffi and beautifulsoup4
motioninput-tui-guides       # fetch anything missing
motioninput-tui-guides --list
motioninput-tui-guides --game sfa3 --force
```

The `guides` extra exists so the trainer never depends on an HTTP stack;
nothing under `guides/` is imported by the app. GameFAQs sits behind Cloudflare,
which is why curl-cffi (browser-like TLS) is preferred over plain requests.

Guides already on disk are never re-fetched, so a normal run makes no requests.
A response under 1KB, or one that looks like an anti-bot page, is treated as a
failure and nothing is written, so a block page can never masquerade as a
reference file.

You do not need the guides to run or develop the trainer; the parsed rosters are
committed. They are only needed to regenerate that data.

## Regenerating character data

The rosters in `src/motioninput_tui/games/data/` are generated from the guides in
`references/` and committed. After changing `datagen/normalise.py` or one of the
parsers, rebuild and commit the JSON:

```bash
motioninput-tui-datagen                # rewrite the JSON
motioninput-tui-datagen --show-skipped # list moves that were not understood
```

Around 80-90% of listed moves become trainable. The rest are follow-ups, stances
and conditional moves ("press P during Ducking") that the trainer has no model
of; they still appear in the move list, struck through.

## Check/Test

```bash
./scripts/run-ci-local.sh   # ty + ruff + pytest, what CI runs
./scripts/run-coverage.sh   # coverage run + html + report
```

### Checking

Run `ruff check` or get the vscode ruff extension, the rules are defined in pyproject.toml.

Ruff runs with `select = ["ALL"]` and `preview = true`, so lint is strict.
Suppressions in this repo use `# ruff: ignore[rule-name] - why` and
`# ty: ignore[rule-name]` rather than `# noqa`, which the preview
`noqa-comments` rule enforces.

### Type Checking

Run `ty`

### Testing

Run `pytest`, It will get its config from pyproject.toml

```bash
pytest tests/test__meta.py::test_repo_url   # a single test
pytest -k logger                            # by name
```

There are no tests for the engine yet. The interesting behaviour is timing
dependent, so tests would want to drive `TrainingSession.press`, `.release` and
`.tick` with explicit timestamps rather than a real clock. Tests for the
inferred path also have to simulate the operating system's auto-repeat stream
(first repeat after the initial delay, then roughly every 33ms); bare presses
without repeats do not reproduce what a real terminal sends and give misleading
results.

### Workflows

The '.github' folder has both a Check and Test workflow.

To get the workflow passing badges on your repo, have a look at <https://docs.github.com/en/actions/monitoring-and-troubleshooting-workflows/adding-a-workflow-status-badge>

Or if you are not using GitHub you can check out workflow badges from your Git hosting service, or use <https://shields.io/> which pretty much covers everything.

### Test Coverage

#### Locally

To get code coverage locally, the config is set in 'pyproject.toml', or run with `pytest`

```bash
python -m http.server -b 127.0.0.1 8000 -d htmlcov
```

Open the link in your browser and browse into the 'htmlcov' directory.

#### Codecov

The template repo uses codecov to get a badge on the README.md, look at their guides on config that up since it's stripped out of this repo.
