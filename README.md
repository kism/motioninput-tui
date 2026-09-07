# motioninput_tui

[![Check](https://github.com/kism/motioninput-tui/actions/workflows/check.yml/badge.svg)](https://github.com/kism/motioninput-tui/actions/workflows/check.yml)
[![CheckType](https://github.com/kism/motioninput-tui/actions/workflows/check_types.yml/badge.svg)](https://github.com/kism/motioninput-tui/actions/workflows/check_types.yml)
[![Test](https://github.com/kism/motioninput-tui/actions/workflows/test.yml/badge.svg)](https://github.com/kism/motioninput-tui/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/kism/motioninput-tui/graph/badge.svg?token=FPGDA0ODT7)](https://codecov.io/gh/kism/motioninput-tui)

A terminal trainer for fighting game motion inputs. Pick a game and a character,
press inputs, and watch which moves come out. The point is that the same input
does different things in different games: hold down and double tap forward in
3rd Strike and you get a dragon punch, do it in Super Turbo or Alpha 3 and you
get nothing.

## Games

| Key      | Game                           | Character source        |
| -------- | ------------------------------ | ----------------------- |
| `hsf2`   | Hyper Street Fighter II        | `references/hsf2.txt`   |
| `sfa3`   | Street Fighter Alpha 3         | `references/sfa3.txt`   |
| `sfiii3` | Street Fighter III: 3rd Strike | `references/sfiii3.txt` |

Each game has its own `Ruleset` in [`games/rulesets.py`](src/motioninput_tui/games/rulesets.py)
describing how forgiving it is: motion windows, whether diagonals can be
skipped, charge times, and whether the dragon punch shortcut exists.

## Run

### Setup

```bash
uv venv
source .venv/bin/activate
uv sync --all-extras # Omit --all-extras for prod
```

### Running the app

```bash
python -m motioninput_tui                              # pick everything in the TUI
python -m motioninput_tui --game sfiii3 --character ryu --layout hitbox
python -m motioninput_tui --list                       # games and characters
python -m motioninput_tui --check-terminal             # terminal suitability
```

## Controls

Two keyboard layouts, chosen on launch. Gamepad support is not implemented, but
the engine talks to an `InputSource`, so adding one means adding a source rather
than touching anything else.

| Layout   | Back / Down / Forward / Up | LP MP HP | LK MK HK |
| -------- | -------------------------- | -------- | -------- |
| Hitbox   | `a` `s` `d` `space`        | `u i o`  | `j k l`  |
| Southpaw | `j` `k` `l` `space`        | `q w e`  | `a s d`  |

In the trainer: `esc` goes back to the picker, `ctrl+r` clears the buffer,
`ctrl+l` toggles the move list, `ctrl+c` quits.

## Terminal choice matters

Motions are judged on wall clock timing, so a terminal that is slow to paint
makes clean inputs read as late. The app identifies your terminal on launch and
warns if it is likely to get in the way.

Comfortable: alacritty, foot, ghostty, kitty, wezterm, contour, rio, st.
Usable: xterm, urxvt, konsole, iTerm2, VTE based terminals, Windows Terminal.
Expect trouble: Terminal.app, the VS Code integrated terminal, Hyper, Tabby.
Running under tmux or screen, or over SSH, adds latency on top of whatever
terminal you are using.

## Keyboard repeat delay

This is the one real compromise. Terminals report key presses and auto-repeats
but **never key releases**, so a held direction has to be inferred from the
repeat stream. A press counts as held for a short window; auto-repeat keeps it
alive beyond that. If your operating system waits a long time before it starts
repeating, that gap is invisible and holds read as taps, which mostly hurts
charge moves.

The trainer measures your repeat delay as you play, widens its window to match
and tells you in the status line if it is worth changing. To fix it at the
source:

```bash
# macOS, then log out and back in
defaults write -g InitialKeyRepeat -int 15
defaults write -g KeyRepeat -int 2

# X11
xset r rate 200 40
```

On Wayland this is a compositor setting (`repeat_delay` in Sway/Hyprland,
Settings → Keyboard in GNOME/KDE).

## Layout

```text
src/motioninput_tui/
  engine/        Device independent: notation, input buffer, motion matchers,
                 rulesets, the recogniser and a training session.
  controls/      Control layouts and input sources. Keyboards today, gamepads later.
  games/         Game metadata, rulesets, move models and the packaged rosters.
  datagen/       Parsers that turn the reference FAQs into games/data/*.json.
  terminal/      Terminal identification and latency warnings.
  tui/           Textual screens and widgets.
```

The engine never touches the clock or the terminal; callers pass timestamps in,
which keeps the matchers straightforward to reason about and to test.

### Regenerating character data

The rosters in `src/motioninput_tui/games/data/` are generated from the FAQs in
`references/` and committed. To rebuild them:

```bash
python -m motioninput_tui.datagen                # rewrite the JSON
python -m motioninput_tui.datagen --show-skipped # list moves that were not understood
```

Around 80-90% of listed moves become trainable. The rest are follow-ups, stances
and conditional moves ("press P during Ducking") that the trainer has no model
of; they still appear in the move list, struck through.

## Check/Test

### Checking

Run `ruff check` or get the vscode ruff extension, the rules are defined in pyproject.toml.

### Type Checking

Run `ty`

### Testing

Run `pytest`, It will get its config from pyproject.toml

There are no tests for the engine yet. The interesting behaviour is timing
dependent, so tests would want to drive `TrainingSession.press` with explicit
timestamps and a simulated auto-repeat stream rather than a real clock.

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
