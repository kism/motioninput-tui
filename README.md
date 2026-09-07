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

For architecture, the data pipeline and the test/lint setup, see
[README_DEV.md](README_DEV.md).

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
motioninput-tui                              # pick everything in the TUI
motioninput-tui --game sfiii3 --character ryu --layout hitbox
motioninput-tui --list                       # games and characters
motioninput-tui --check-terminal             # terminal speed and key release support
motioninput-tui --no-key-release             # force the auto-repeat fallback
motioninput-tui --loose-buffer               # let inputs feed more than one move
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
`ctrl+l` toggles the move list, `ctrl+b` toggles the buffer rule, `ctrl+c` quits.

## Spending inputs

When a special comes out, the games clear the command buffer so the inputs that
produced it cannot go on to feed another move. Without that, two fireballs in a
row would read as the double quarter circle of a super. Normals and throws do
not clear it, matching the games.

Steps of a motion also have to be close together, not merely finish inside a
time limit. The forward you are still holding after a fireball is genuinely
still held, so without a per-step limit a later down, down-forward would turn it
into a dragon punch.

`--loose-buffer`, or `ctrl+b` in the trainer, turns both off. Inputs are then
reused freely and one motion can light up several moves at once. No game behaves
that way, but it is a useful way to see everything your inputs contain.

## Terminal choice matters

Motions are judged on wall clock timing, so a terminal that is slow to paint
makes clean inputs read as late. The app identifies your terminal on launch and
warns if it is likely to get in the way.

Comfortable: alacritty, foot, ghostty, kitty, wezterm, contour, rio, st.
Usable: xterm, urxvt, konsole, iTerm2, VTE based terminals, Windows Terminal.
Expect trouble: Terminal.app, the VS Code integrated terminal, Hyper, Tabby.
Running under tmux or screen, or over SSH, adds latency on top of whatever
terminal you are using.

## Key releases

A plain terminal only ever tells you a key went _down_. That is a problem for a
motion input trainer, because knowing when the player let go of down is the
difference between a fireball and a dragon punch.

The trainer handles this two ways, and picks the better one available.

### Exact tracking (preferred)

The **kitty keyboard protocol** adds an event type to each key report, so the
terminal reports releases as well as presses. Where it is available, holds are
tracked exactly, motions are judged against the games' real timing windows, and
your keyboard repeat settings stop mattering entirely. The status line says
`exact key tracking` when this is active.

Supported by kitty, Ghostty, foot, WezTerm, Alacritty, Contour and Rio. Check
yours with:

```bash
motioninput-tui --check-terminal
```

Pass `--no-key-release` to turn it off and use the fallback instead.

### Inferred holds (fallback)

Without release reporting, a held direction has to be deduced from the
auto-repeat stream. A press counts as held for a short window and auto-repeat
keeps it alive beyond that. If your operating system waits a long time before it
starts repeating, that quiet gap is invisible and holds read as taps, which
mostly hurts charge moves.

The trainer measures your repeat delay as you play, widens its window to match,
and says so in the status line. To fix it at the source:

```bash
# macOS, then log out and back in
defaults write -g InitialKeyRepeat -int 15
defaults write -g KeyRepeat -int 2

# X11
xset r rate 200 40
```

On Wayland this is a compositor setting (`repeat_delay` in Sway/Hyprland,
Settings → Keyboard in GNOME/KDE).

### What about reading the keyboard device directly?

Possible, but worse. `evdev` on Linux needs root or the `input` group and does
not work on macOS; Quartz event taps on macOS need Input Monitoring permission
and read every keystroke system-wide, including ones meant for other
applications. The kitty protocol gets the same information with no permissions,
no elevated privileges, and it keeps working over SSH.
