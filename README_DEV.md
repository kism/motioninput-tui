# motioninput_tui development

Architecture, the character data pipeline, and the check/test setup. For
installing and using the trainer, see [README.md](README.md).

## Layout

```text
src/motioninput_tui/
  config.py      Last used selection, saved under ~/.config/motioninput-tui/.
  gamepad_probe.py  `python -m ...gamepad_probe`: dumps a pad's SDL state to /tmp.
  engine/        Device independent: notation, input buffer, motion matchers,
                 rulesets, the recogniser and a training session.
  controls/      Control layouts and input sources: keyboard, plus a gamepad
                 (optional `gamepad` extra) polled from the training tick.
  games/         Game metadata, rulesets, move models and the packaged rosters.
  datagen/       Parsers that turn the reference FAQs into games/data/*.json.
  terminal/      Terminal identification, latency warnings, kitty keyboard protocol.
  tui/           Textual screens, widgets, and the release-aware input driver.

src/motioninput_tui_guides/   Fetches the FAQs from GameFAQs. A sibling package,
                              not a subpackage, so it is not shipped in the wheel.
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
page or a corrupt copy is caught before the parsers run. When a guide really has
changed and the new text is correct, update the checksum from
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
committed. They are only needed to regenerate that data.

### Concise guides

Each guide also has a condensed twin at `references/<game>_concise.txt`, about a
quarter the size, holding the roster, the move lists, the notation key and
anything the guide says about how the game reads inputs. It is what to read when
adding a game, rather than wading through the full FAQ.

```bash
./scripts/run-concise-guides.sh              # every guide that lacks one, then check them
./scripts/run-concise-guides.sh --force sfa3 # redo one
```

That condenses each guide by running the `claude` CLI over it in chunks, then
checks the result by parsing both the full and the concise file and comparing the
rosters, which is a real check for the three games that already have parsers.
Guides that already have a concise version are skipped, so the bare command is
cheap to repeat. See [the skill](.claude/skills/concise-guides/SKILL.md) for what
it keeps and why. These files are derived from the guides, so they are gitignored
and not redistributable either.

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

### Character names

The guides disagree about what characters are called, so
[`datagen/names.py`](src/motioninput_tui/datagen/names.py) holds the names to
use instead, per game:

```python
OVERRIDES: dict[str, dict[str, str]] = {
    "sfa3": {"ken-masters": "Ken", "edmond-honda": "E. Honda", ...},
    "sfiii3": {"gouki": "Akuma", ...},
}
```

The left hand side is the key the guide produced and the right hand side is the
name to display. Keys are rebuilt from the new name, so this renames
`ken-masters` to `ken` everywhere, including `--character` and the saved config.
Two guides naming the same character differently is the main reason to reach for
this: 3rd Strike's says Gouki where Super Turbo's says Akuma.

An entry that matches nobody logs a warning rather than passing silently, and so
does a rename that collides with another character's key. Rerun the generator
afterwards and commit the JSON.

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
  test_hierarchy.py  Guards the layout below.
  sfiii3/test_elena.py   3rd Strike, Elena.
  sfiii3/test_ryu.py     3rd Strike, Ryu.
  sfa3/test_ryu.py       Alpha 3, Ryu, same scripts and different answers.
```

The directory is the game key and the file name is the character key, with
underscores for the hyphens in the rosters (`test_chun_li.py` is
`chun-li`). The `play` fixture reads both out of the path, so a test never
names them and cannot be run against the wrong character. `test_hierarchy.py`
fails if a directory is not a game or a file is not one of its characters.

To add coverage, make the directory for the game if it is missing and write
`test_<character>.py` in it:

```python
from tests.engine.test_motions.harness import DOWN, FORWARD, HP, press, release


def test_quarter_circle_forward_is_a_fireball(play) -> None:
    attempt = play([press(DOWN, 0), press(FORWARD, 70), release(DOWN, 110), press(HP, 150)])
    assert attempt.directions == "↓ ↘ →"
    assert attempt.moves == ["Hadou Ken"]
```

Scripts are timestamped by hand rather than run against a real clock, and they
go in at the key level, so SOCD cleaning and the direction states it produces
are covered as well as the matchers. `attempt.directions` is the input strip as
arrows, which is what makes a failure readable. Inputs meant to be compared
across games live in `harness.py` so that all three games are demonstrably
being given the same keys at the same moments.

Play defaults to `exact_input=True`, which is the terminal reporting key
releases. A test for the inferred path has to pass `exact_input=False` and
simulate the operating system's auto-repeat stream itself (first repeat after
the initial delay, then roughly every 33ms); bare presses without repeats do
not reproduce what a real terminal sends and give misleading results.

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
