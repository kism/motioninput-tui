# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Textual TUI for practising fighting game motion inputs. You pick a game and a
character, press inputs, and it shows which move the game would have given you.
The whole point is that the same input differs per game: in 3rd Strike holding
down and double tapping forward gives a dragon punch, in Alpha 3 and Super
Turbo it gives nothing.

See `README.md` for a quick start, and the full documentation at
`docs/index.md` (Sphinx + MyST, so the pages are Markdown; published to Read
the Docs) for using the trainer, `docs/development.md` for the developer
setup, and `docs/adding-a-game.md` for adding a new title — also available as
the `add-a-game` skill. This file covers what is hard to discover from the
code alone.

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
python -m motioninput_tui.gamepad_probe                    # dump a pad's SDL state to /tmp (ctrl+c to stop)
python -m motioninput_tui --list                           # rosters
python -m motioninput_tui.datagen --show-skipped           # rebuild packaged rosters
python -m motioninput_tui_guides --list                    # reference guide catalogue
```

When adding a game, read `references/<game>_concise.txt` rather than the full
guide: same roster, move lists, notation key and input-behaviour notes, about a
quarter of the size. The `concise-guides` skill makes any that are missing and
verifies them by parsing both files and comparing rosters. They are derived from
the guides, so they are gitignored and must not be committed or quoted either.
The `add-a-game` skill walks the whole procedure end to end; `docs/adding-a-game.md`
is the same walkthrough for a person.

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

Python 3.14+ only. Use modern type hints throughout: `list[str]`, `X | None`,
`from collections.abc import ...`, and the plain built-in generics. Never add
`from __future__ import annotations` — the runtime is new enough that it buys
nothing, and existing files are being cleaned of it.

## Config

`config.py` remembers the last game, character, layout, settings and buffer
policy in `~/.config/motioninput-tui/config.json` (honouring `XDG_CONFIG_HOME`). It is
best-effort throughout: a missing, corrupt or unwritable file logs and falls
back to defaults rather than raising. `Config` doubles as the app's starting
selection and its persistence, which is why `MotionInputApp` takes one instead
of separate game/character/layout arguments.

Key release support is deliberately not persisted; it is probed per terminal
each launch.

Setting `OptionList.highlighted` queues a highlight event, and an OptionList
also posts one for index 0 when options are added. `SetupScreen` and
`InputPickerScreen` therefore apply the remembered selection from
`call_after_refresh`, not `on_mount`, or the queued events overwrite it. Focus
is set there too, since the character list has no options until then.

### Global settings

`settings.py` is the player's own preferences, as opposed to a game's rules or a
device's timings. Each one is a `Setting` naming a **boolean attribute of
`Config`**, which is what lets the settings pane read and write them by name
without knowing what any of them mean; `buffer_policy` is an enum, so
`Config.loose_buffer` bridges it. `tuned_game` folds the ones that change
matching into the game's ruleset, so everything downstream still just reads
`game.ruleset` and nothing else has to know the player has a say in it.

Adding one: a boolean field on `Config` (loaded through `_valid_flag`, saved in
`save`), an entry in `SETTINGS`, and, if it changes matching, a `Ruleset` field
plus a line in `tuned_game`. Nothing in the interface needs touching.

### Move notation

`notation_styles.py` is how a move's input is *written*, as opposed to
`engine/notation.py`, which is what a direction *is*. A `Notation` holds one
`Style` per `Family` (directions, quarter, half, dragon, rotate, charge) and
writes a `MotionSpec` by parts: each part is either a glyph the player picked
for its family or the directions spelled out, so a compound motion follows its
parts' styles for free. A style with no glyph for a kind spells that kind out,
which is what makes the first style of every family the plain one. Moves with
no `MotionSpec`, and `MotionKind.ANY`, keep the guide's own wording.

The live input strip never consults it: what the player pressed is always
arrows, deliberately, so one reading of the display never changes.

Adding a style is a row in `STYLES` — nothing else, since the config validator
takes its vocabulary from that table and the menu previews whatever is in it. A
`Family.DIRECTIONS` style carries a direction table and a separator instead of
glyphs, which is how numpad (`236`, the `Direction` enum's own values, joined by
nothing) and the emoji and nerd font variants are written.

Nerd font codepoints come from `glyphnames.json` in the nerd-fonts repository,
downloaded rather than committed (it is gitignored). Every one in the source is
commented with the glyph name it came from, so it can be checked against a fresh
copy.

`tui/widgets/settings_list.py` is the toggles themselves, shared by the setup
screen's pane and the trainer's `ctrl+b` modal. It posts `SettingsList.Changed`,
which bubbles past both to `MotionInputApp.on_settings_list_changed`: that saves
it and, if a session is running, calls `TrainingScreen.apply_settings` so the
change lands mid-session rather than at the next one.

Space toggles, not enter: enter belongs to the screen the list sits on (start
training, or close the modal), so both hosts bind it with `priority=True` and
the widget never sees it. A mouse click still toggles, which is why the widget
keeps handling `OptionSelected` — and stops it, so a host that treats a
selection on its other lists as a choice cannot act on it too.

## Architecture

Dependencies point one way: `engine` ← `controls` ← `games` ← `tui`.

The screens run input picker → setup → trainer, with two modals over them:
`ctrl+b` for the settings and `ctrl+n` for the move notation, both opened by an
action on the app (`app.settings`, `app.notation`) so any screen can offer them
and the app, which owns the config, is the one that saves what comes back. The input picker is on its own
because the device decides how the trainer reads you, not what you are training;
it owns the gamepad detection and the `b` rebind modal. The setup screen is the
three panes of what to train: settings, game, character. Escape steps back one
screen (trainer → setup → input picker); each screen dismisses and the app
pushes the next, so the stack never grows.

**`engine/` is device and terminal agnostic and never reads a clock.** Callers
pass `at_ms` timestamps in. `engine/recognizer.py` takes moves through a
`RecognisableMove` Protocol rather than importing `games`, which is what keeps
that direction clean. Preserve this: it is why the matchers can be driven
deterministically.

Reading order for the interesting parts: `engine/notation.py` (numpad
directions, player on the left, so 6 is forward) → `engine/buffer.py` →
`engine/motions.py` → `engine/ruleset.py` → `engine/recognizer.py` →
`engine/session.py`.

### Layouts, button sets and the input display

A `ControlLayout` is *where* the attacks are: `attack_rows`, two rows of key
codes. A `ButtonSet` (`controls/buttons.py`) is what those positions *mean*,
also as rows, and `with_buttons` lays one onto the other position by position.
That is the whole mechanism: a game with a different panel is a table entry, not
a new layout per keyboard arrangement. A button appearing in both rows of a set
is how the Neo Geo binds `asdf` and `zxcv` to the same four.

`Button` therefore holds every game's buttons, but `ALL_BUTTONS` is still only
the Street Fighter six: it is what a *roster* can ask for, and the generated
data is Street Fighter. Widening it would change what "any button" means in the
move lists.

Layouts are built carrying the six, so `app._panel_for` only lays a set on when
it is not that one — which is also what keeps a rebound gamepad from being
flattened back to its defaults, since the rebind screen only knows those six.

The first game in the list, `display`, has no roster: `loader._display_game`
builds it, and its characters *are* the button sets, which is how a panel gets
picked with the same two lists as everything else. `InputDisplayScreen` runs a
real `TrainingSession` (so SOCD and holds behave exactly as in the trainer) and
draws the panel instead of recognising anything. The Neo Geo's two arrangements
are a global setting rather than two entries, applied by `buttons.arrangement`.

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

A gamepad is always exact. `controls/gamepad.py` polls pygame from the training
tick, diffs the pad's state, and feeds presses and releases through the same
`KeyboardSource` (in `exact=True` mode) that the keyboard uses — there is no
separate source. pygame is the optional `gamepad` extra; everything degrades to
"no gamepad" when it is missing or nothing is plugged in. On macOS pygame only
sees pads under the real Cocoa video driver, so `_load_pygame` skips the `dummy`
driver there and sets `SDL_MAC_BACKGROUND_APP` instead.

**Read the pad through SDL's game-controller API, not raw joystick buttons.**
`_first_controller` opens a `pygame._sdl2.controller.Controller`, so
`codes_from_pad` reads `CONTROLLER_BUTTON_A`/`X`/… and SDL's controller
database maps each pad's real (often bizarre) button numbering onto the
Xbox-style layout. Reading `joystick.get_button(0..5)` is what made most of the
buttons dead. Tests drive `codes_from_pad` with a `FakePad`; a root autouse
fixture stubs `_first_controller` so a plugged-in pad never leaks in.

The eight attack codes (`pad:0`-`pad:5` face/shoulder, `pad:6`/`pad:7`
triggers) start on a fixed Xbox-style default (`GAMEPAD_DEFAULT_BINDINGS` in
`controls/layouts.py`, six of the eight). `b` on the setup screen's gamepad row
opens `tui/screens/gamepad_bind.py` to remap them; `SetupScreen` also renames
that row after the connected pad. The map is stored in `config.json` as
`gamepad_bindings` (`{button name: pad code}`) and applied by `gamepad_layout()`,
which falls back to the default whole rather than leave an attack unreachable.
Movement (d-pad + left stick) is not rebindable.

`decay_ms` is the bridge between them: how long the device takes to reveal a
release. Zero when exact, `tap_ms` when inferred. It is threaded
session → recogniser → `MatchContext` → matchers, where it widens motion
windows and step gaps. Without it, inferred holds would make every motion look
too slow to land.

### Three kinds of tuning constant, easily confused

* `engine/ruleset.py` / `games/rulesets.py` — **game** behaviour. Motion
  windows, whether diagonals can be skipped, charge times, `dp_double_tap`
  (the headline SF3 difference). Per game.
* `controls/layouts.py` `HoldTiming` — **device** behaviour. Nothing to do with
  which game is selected.
* `settings.py` — the **player's** choice, whichever game is selected.
  `lenient_half_circles` lives on `Ruleset` because that is what the matchers
  read, but its value comes from the player, not the game.

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
