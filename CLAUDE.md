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

## Writing documentation

Keep it short, and do not write what the program already says.

The app documents itself: every screen has a `Footer` listing its keys, the
setup pane and the `ctrl+b` modal print each setting's name, state and
`Setting.detail`, the `ctrl+n` menu draws every notation style as its own
preview, and the pickers list the games, characters and layouts. Anything in
that list belongs in the code that renders it, not in `docs/` — a table of
settings or glyphs in Markdown is a second copy that goes stale silently and
tells a reader nothing they would not see by pressing the key.

Documentation is for what the app cannot show: why a game's rules differ, what
the config file remembers and where it lives, gotchas the interface has no room
to explain, and anything about the terminal or the operating system that has to
be fixed outside the program. Prefer a sentence to a table and a paragraph to a
section. If a change makes a doc longer, check whether it should instead make
the app clearer.

## Commands

```bash
uv sync --all-groups            # dev setup; omit --all-groups for prod

.venv/bin/ruff format .         # format
.venv/bin/ruff check --fix .    # lint
.venv/bin/ty check .            # type check
.venv/bin/pytest -q -n auto     # tests, in parallel (xdist); coverage stays serial
./scripts/run-ci-local.sh       # ty + ruff + pytest, what CI runs
./scripts/run-coverage.sh       # coverage run + html + report
.venv/bin/python .claude/skills/prepare-release/check-docs.py   # docs + in-app text, before a release
./scripts/2-game-briefs.sh      # analyse any guide lacking .claude/skills/game-brief/briefs/<game>.md
./scripts/4-run-datagen.sh      # rebuild packaged rosters from references/ (wraps python -m motioninput_tui_datagen)
python -m motioninput_tui_datagen --summary   # per-character move / trainable counts for the data on disk

.venv/bin/pytest tests/test__meta.py::test_repo_url        # a single test
.venv/bin/pytest -k logger                                 # by name
.venv/bin/pytest tests/engine/test_motions/sfiii3          # one game's motion tests

python -m motioninput_tui                                  # run it
python -m motioninput_tui --check-terminal                 # speed + key release support
python -m motioninput_tui.gamepad_probe                    # dump a pad's SDL state to /tmp (ctrl+c to stop)
python -m motioninput_tui --list                           # rosters
python -m motioninput_tui_datagen --show-skipped           # rebuild rosters, listing moves that would not normalise
python -m motioninput_tui_guides --list                    # reference guide catalogue

./scripts/decode-3s-commands.py ~/src/3s-decomp [character]   # print 3rd Strike's real command tables
```

When adding a game, read its brief at `.claude/skills/game-brief/briefs/<game>.md`
first. It is analysis, not a copy of the guide: the roster and which sections to
skip, the guide's layout for the parser, the button and motion gotchas with a
predicted trainable rate, a proposed `Ruleset`, and motion-test seeds. The
`game-brief` skill writes one per guide (a single `claude -p` pass over the full
guide, reasoning against the engine files) and verifies it. Briefs *are*
committed — they name characters and quote the odd input, never whole move
lists. The datagen parser is still written against the full
`references/<game>.txt`, whose fixed-width layout it keys off. The `add-a-game`
skill walks the whole procedure end to end; `docs/adding-a-game.md` is the same
walkthrough for a person.

`src/motioninput_tui_guides/` fetches `references/*.txt` from GameFAQs, and
`src/motioninput_tui_datagen/` parses them into `games/data/*.json`. Both are
sibling packages rather than subpackages so `uv_build` (which packages only the
one module matching the project name) leaves them out of the wheel; keep it that
way, and do not give either a console script — run them as
`python -m motioninput_tui_guides` / `python -m motioninput_tui_datagen`, or via
`scripts/1-download-guides.sh` / `scripts/4-run-datagen.sh`. The guides package's
dependencies live in the `guides` group (`uv sync --group guides`); datagen needs
nothing beyond the trainer itself. The fetched guides are copyrighted, gitignored,
and must never be committed or quoted back into the repo; only the parsed rosters
under `games/data/` are.

Ruff runs with `select = ["ALL"]` and `preview = true`, so lint is strict.
Suppressions in this repo use `# ruff: ignore[rule-name] - why` and
`# ty: ignore[rule-name]`, not `# noqa`; the preview `noqa-comments` rule
enforces that.

Python 3.14+ only. Use modern type hints throughout: `list[str]`, `X | None`,
`from collections.abc import ...`, and the plain built-in generics. Never add
`from __future__ import annotations` — the runtime is new enough that it buys
nothing, and existing files are being cleaned of it.

## Config

`config.py` remembers the last game, character (per game, in `characters`;
`save` folds the current selection into it), layout, settings, buffer policy
and the pad / custom-keyboard rebinds in `~/.config/motioninput-tui/config.json`
(honouring `XDG_CONFIG_HOME`). It is best-effort throughout: a missing, corrupt
or unwritable file logs and falls back to defaults rather than raising.
`_LAYOUT_ALIASES` migrates a pre-rework `hitbox` / `southpaw` layout on load. `Config` doubles as the app's starting
selection and its persistence, which is why `MotionInputApp` takes one instead
of separate game/character/layout arguments.

Key release support is deliberately not persisted; it is probed per terminal
each launch.

The config file is the *only* place the selection lives. The command line is
`--config`, `--list`, `--check-terminal`, `--version` and `-v`: `--game`,
`--character`, `--layout`, `--loose-buffer` and `--no-key-release` were all
removed, because a flag and a remembered value saying different things needs a
precedence rule, and none of them earned one. `tests/test_cli.py` guards the
surface, so re-adding one is a deliberate act rather than a drift.

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
`Config.loose_buffer` bridges it. None of them changes how a game's inputs are
matched: that is the game's `Ruleset`.

Adding one: a boolean field on `Config` (loaded through `_valid_flag`, saved in
`save`) and an entry in `SETTINGS`. Nothing in the interface needs touching.

### Move notation

`notation_styles.py` is how a move's input is *written*, as opposed to
`engine/notation.py`, which is what a direction *is*. A `Notation` holds one
`Style` per `Family` (directions, quarter, quarter_down, half, dragon, tiger, rotate, charge, mark) and
writes a `MotionSpec` by parts: each part is either a glyph the player picked
for its family or the directions spelled out, so a compound motion follows its
parts' styles for free. A style with no glyph for a kind spells that kind out,
which is what makes the first style of every family the plain one. Moves with
no `MotionSpec`, and `MotionKind.ANY`, keep the guide's own wording.

The live input strip never consults it: what the player pressed is always
arrows, deliberately, so one reading of the display never changes. The motion
rows the trainer and the input display draw over their history do,
since they name motions rather than record presses, and so does the stick on
the live panel, whose boxes are labelled in the direction style.

Adding a style is a row in `STYLES` — nothing else, since the config validator
takes its vocabulary from that table and the menu previews whatever is in it. A
`Family.DIRECTIONS` style carries a direction table and a separator instead of
glyphs, which is how numpad (`236`, the `Direction` enum's own values, joined by
nothing) and the emoji and nerd font variants are written. A motion family's
style can carry a direction table too, and then spells just that family out in
it: that is each family's Numpad, the same `Style` Directions offers. A `Family.MARK` style
is not a motion at all: it carries one `mark`, what those motion rows put over
a throw, a command normal or a counted mash tap.

Nerd font codepoints come from `glyphnames.json` in the nerd-fonts repository,
downloaded rather than committed (it is gitignored). Every one in the source is
commented with the glyph name it came from, so it can be checked against a fresh
copy.

`tui/widgets/settings_list.py` is the toggles themselves, shared by the setup
screen's pane and the trainer's `ctrl+b` modal. It posts `SettingsList.Changed`,
which bubbles past both to `MotionInputApp.on_settings_list_changed`: that saves
it and, if a session is running, hands the buffer policy to its
`apply_settings` so the change lands mid-session rather than at the next one.

Space toggles, not enter: enter belongs to the screen the list sits on (start
training, or close the modal), so both hosts bind it with `priority=True` and
the widget never sees it. A mouse click still toggles, which is why the widget
keeps handling `OptionSelected` — and stops it, so a host that treats a
selection on its other lists as a choice cannot act on it too.

The same split holds on every screen: space acts on the highlighted row
(flips a setting, picks a notation style, arms a rebind) and enter confirms the
screen, bound with `priority=True` so the `OptionList`'s own enter never fires.

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

`tests/test__meta.py` holds that direction to it: `engine` may not import
`games` or `tui` at runtime (a `TYPE_CHECKING` import is fine, and
`engine/session.py` uses one), and no game key may appear in engine code. A
game's rules reach the matchers as `Ruleset` values, never as a branch. This
matters most when one game's behaviour is better understood than the rest's -
see `docs/sfiii3-from-the-decomp.md`, where nine `Ruleset` fields default to
off precisely so that what is known about one game stays opt-in.

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
the Street Fighter six: that is the one dialect `normalise` parses into, and a
roster on another panel has its requirements mapped off it afterwards by
`datagen/neogeo.py`. Widening it would change what "any button" means in every
move list at once.

Layouts are built carrying the six, so `app._panel_for` only lays a set on when
it is not that one — which is also what keeps a rebound gamepad from being
flattened back to its defaults, since the rebind screen only knows those six.

The picker offers two keyboard presets (`KB_LEFT` / `KB_RIGHT`) and a
`KB_CUSTOM` whose keys — all four directions and the six attacks — are set from
`tui/screens/keyboard_bind.py` (`b` on that row), stored as
`config.keyboard_bindings` (`{slot: key name}`) and applied by
`keyboard_layout()`, exactly parallel to `gamepad_bindings` / `gamepad_layout`.
`resolve_keyboard_bindings` falls back to the default map whole if two slots
collide. Key names are Textual's (`comma`, `semicolon`, `space`); `friendly_key`
turns them back into glyphs for display. `HITBOX` / `SOUTHPAW` stay as module
constants — the four-key reference layouts the engine test harness and
`tests/controls/test_buttons.py` are written against — but are out of `LAYOUTS`.

Every roster opens with the input display, a character `loader._input_display`
builds rather than one from a guide (`INPUT_DISPLAY` is its key): its moves are
every motion in the game, on any of the game's buttons and without their
follow-throughs, so a press on whatever the stick made brings it out.
`InputDisplayScreen` runs a real `TrainingSession` (so SOCD and holds behave
exactly as in the trainer), and has the trainer's bottom row, a `LivePanel`:
the stick and the buttons beside the history, with the session's trail over it. `datagen --summary`
leaves it out of the counts. A panel is only reached through a game played on
it, so the Mortal Kombat, Tekken and eight button sets are defined but offered
nowhere. The Neo Geo's two arrangements are a global setting rather than two
entries, applied by `buttons.arrangement`.

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
separate source. pygame is a base dependency but imported lazily; everything
degrades to "no gamepad" when it is missing or nothing is plugged in. On macOS pygame only
sees pads under the real Cocoa video driver, so `load_pygame` skips the `dummy`
driver there and sets `SDL_MAC_BACKGROUND_APP` instead.

**Read the pad through SDL's game-controller API, not raw joystick buttons.**
`_first_controller` opens a `pygame._sdl2.controller.Controller`, so
`codes_from_pad` reads `SDL_GameControllerButton` values — spelled out as the
`_BUTTON_A`/`_BUTTON_X`/… constants at the top of the file rather than taken
from pygame, which keeps it a plain function the tests can drive — and SDL's
controller database maps each pad's real (often bizarre) button numbering onto
the Xbox-style layout. Reading `joystick.get_button(0..5)` is what made most of the
buttons dead. Tests drive `codes_from_pad` with a `FakePad`; a root autouse
fixture stubs `_first_controller` so a plugged-in pad never leaks in.

The eight attack codes (`pad:0`-`pad:5` face/shoulder, `pad:6`/`pad:7`
triggers) start on a fixed Xbox-style default (`GAMEPAD_DEFAULT_BINDINGS` in
`controls/layouts.py`, six of the eight). `b` on the input picker's gamepad row
opens `tui/screens/gamepad_bind.py` to remap them; `InputPickerScreen` also
renames that row after the connected pad. The map is stored in `config.json` as
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
  (the headline SF3 difference), `super_freeze_ms`. Per game. Third Strike's
  figures are the only ones not estimated: they are read out of the
  decompilation, and `docs/sfiii3-from-the-decomp.md` says where each comes from
  and what is still open. Do not "tidy" them towards the other games.
* `controls/layouts.py` `HoldTiming` — **device** behaviour. Nothing to do with
  which game is selected.
* `settings.py` — the **player's** choice, whichever game is selected.

### Spending inputs

Games flush the command buffer when a special activates. Two mechanisms
enforce this together, and both are needed:

* `InputBuffer.consume()` on activation (normals and throws do not flush,
  matching the games).
* `Ruleset.step_gap_ms` bounds the pause between consecutive steps of a motion.
  A total-span limit is not enough on its own: the forward you are still
  holding after a fireball survives the flush, and without a per-step limit a
  later `d, df` would turn it into a dragon punch.

`BufferPolicy.LOOSE` (the loose buffer setting, `ctrl+b`) disables both.

### Two-phase moves

A `MotionSpec.mash` tail (`qcf,qcf + P, tap P rapidly`, or `f,d,df + K,
tap P,P,P` with `mash_rhythm` — deliberate taps rather than a mash, sometimes on
a different button, `mash_button`) is *not* a match gate. The motion activates
on its own — phase 1, a normal `Activation` that counts — and the recogniser
opens a `FollowUp` (`recognizer.py`) on it. Later taps of the right button
advance it to `COMPLETE`; `Recognizer.advance_follow_up`, driven from the session
tick, flips it to `MISSED` once the window passes. The same `FollowUp` object is
held by the `Activation` in the feed, so `MoveFeed` shows the live prompt and
the verdict. `_priority` still gives a tail move `+1` so it wins `hits[0]` over
its tail-less twin.

**A super's tail waits out the cinematic.** `Ruleset.super_freeze_ms` is how
long the activation freeze runs, and the game reads nothing while it does, so
the whole second phase — the first tap, the gap the rhythm variant wants, the
deadline — is measured from the end of it rather than from the press. A press
inside it is swallowed whatever it was: it cannot count as a tap, and it cannot
be judged as abandoning them. `advance_follow_up` is also what clears
`FollowUp.frozen` when the freeze passes, which is how `MoveFeed` knows to say
`wait...` rather than prompting for taps a frozen game will not read.

This applies to `category == "super"` only. A *special* with a mashable tail
(Sakura Otoshi, Dee Jay's Machinegun Upper, Kensou's Ryuu Renda) has no
cinematic and is read at once, which is what `recognizer.SUPER_CATEGORY`
compares against — a plain string, because `engine` never imports `games`.

### One Super Art at a time

3rd Strike equips one Super Art of three, and 18 of its 20 characters have two
or three supers on one identical motion and button — 14 of them on `qcf,qcf + P`
alone. Other games do have the odd pair (four characters in KoF '98, two in
2001, two in USFIV, Akuma in Alpha 3), but nothing on this scale and nothing
with a mechanism to tell them apart. So `Move.super_art` carries the guide's
`I`/`II`/`III` flag (the `sfiii3` parser already matched it, it was just being
thrown away) and
`TrainingSession._live_moves` hands the recogniser only the equipped one.
`tab` on the trainer cycles them.

This is what makes the clash tractable at all, and it is also why the two-phase
tail above stays cheap: with one Super Art equipped nobody has two supers on one
input — Akuma comes closest, with a ground and an air super under both SA I and
SA III, and the `air` flag separates those — so the follow-up only ever opens
for a move that genuinely wants the taps.

Ultra SF4 uses the same field for its two Ultra Combos, which are picked before
a match the same way: `Character.super_arts` is `("I", "II")` there, and Metsu
Hadouken and Metsu Shoryuken are the pair it separates. Everywhere else — and
for Gill, the one 3rd Strike character without a choice — `super_arts` is empty
and the mechanism turns into a no-op: the filter passes everything and
`check_action` hides the `tab` binding.

### SOCD is neutral on a keyboard, and only where releases are reported

A keyboard whose terminal reports releases cancels opposite cardinals, as
GP2040-CE's SOCD neutral does: left, down and right together are down. Where
holds are inferred, `direction_from_axes` falls back to newest-wins for
left+right, and up beats down. That fallback is a correctness requirement, not a style choice: that
terminal cannot see you release back as you press forward, so both look held
during ordinary motions, and neutral there would make charge moves impossible.
A pad is not cleaned: its d-pad cannot hold both ways, so newest-wins only
settles the stick against the d-pad.

`InputBuffer.set_direction` (and the strip) drops a direction replaced in the
millisecond it arrived, since a controller is read all at once. That is what
lets a test script swap back for forward with a release and a press at the
same moment, rather than detouring through down or neutral.

### Two rotation rules

**Third Strike's is known.** `_match_rotation_cardinals` is `check_6` from the
decompilation: a set of which of the four cardinals have been seen, compared for
equality so no diagonal ever counts towards one, in any order. Two timers wipe
that set — `rotation_cardinal_gap_ms` without the lever resting on a cardinal,
and `rotation_window_ms` for the turn. A neutral is not special; it only costs
the time it takes, so four separate taps *are* a 360 if they are quick enough.
What makes one hard is the pace, and the jump. `rotation_slack` is not read.

`Ruleset.jump_grace_ms` is that jump, and it is not a rotation rule: up is a
jump input, so `_match_ground` in `motions.py` blocks *every* grounded move for
`AIR_MEMORY_MS` after one, leaving only the jump's startup frames for the button
to land in. It mirrors `_match_air`, which is what makes an air move count over
the same span — exactly one of the two passes at a time, which is the game's own
`xyz[1].disp.pos <= 0` test. Rotations opt out and judge it per turn, since a
circle cannot avoid an up.

**Every other game's is reckoned.** `_match_rotation` accumulates how far round
the ring the stick has travelled rather than demanding all eight directions, so
a hitbox rolling through four keys gets its diagonals from the overlap and
counts, and a `NEUTRAL` resets that travel to zero. `rotation_slack` tunes which
directions may be missed, and 2 is as loose as it should get: at 3 a half circle
back carried one notch past back is a whole revolution.

The travel model was written to stop the trainer handing out Hugo's Moonsault
Press too freely, which was the right complaint about the wrong mechanism — 3rd
Strike's own answer is the pace, not the neutral. It stays for the games there is
no decompilation to check, and should be replaced per game as data arrives
rather than tidied to match Third Strike.

### Rosters are generated and committed

`games/data/*.json` is produced from the guides in `references/` by the
`motioninput_tui_datagen` sibling package. Those guides are gitignored, so a
fresh clone has to run `python -m motioninput_tui_guides` first. After changing
`motioninput_tui_datagen/normalise.py` or a parser in
`motioninput_tui_datagen/parsers/`, rerun `python -m motioninput_tui_datagen`
(or `./scripts/4-run-datagen.sh`) and commit the JSON. The Street Fighter
rosters land around 80-90% trainable; the SNK ones are lower (52% for Samurai
Shodown II, 68-75% for the rest) because those guides lean on command throws
written `b or f + button` and on long follow-up chains. The remainder are
follow-ups and conditional moves that still appear in the move list, struck
through. `--summary` prints the per-character breakdown.

The guides disagree about character names, so `motioninput_tui_datagen/names.py` maps the key a
guide produced to the name to use instead, per game (`ken-masters` → `Ken`).
Keys are rebuilt from the new name, so an override renames the character
everywhere, including anyone's saved config — which is why `__main__` forgets a
remembered character that is no longer in the roster instead of refusing to
start.

`motioninput_tui_datagen/commands.py` is the same idea for a guide that has a
move's *input* wrong, keyed `(character key, move name)` and applied after
`names.py` so the key is the one the roster ends up with. The replacement goes
through the ordinary `parse_command`, so it is written the way a guide would
write it. Reserve it for outright errors checked against the real game: a
command the parser merely cannot model belongs in `normalise`'s tables, or stays
untrainable and struck through.

This is worth more care than a wrong name, because a wrong command does not look
like a bug. Sakura's Midare-zakura in Alpha 3 is the entry: the guide gives
`qcf,d,df + K`, which parsed cleanly and came out perfectly well in the trainer —
it was simply not the move. Only playing the game finds these, so the overrides
carry a note saying what was checked.

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
never name a game or a character; `test__meta_hierarchy.py` fails on a directory that
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
