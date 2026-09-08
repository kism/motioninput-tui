# motioninput-tui

A terminal trainer for fighting game motion inputs. Pick a game and a character,
press inputs, and watch which moves come out. The point is that the same input
does different things in different games: hold down and double tap forward in
3rd Strike and you get a dragon punch, do it in Super Turbo or Alpha 3 and you
get nothing.

See [Adding a game](adding-a-game.md) to add another title, or
[Development](development.md) for the architecture and the check/test setup.

## Games

| Key       | Game                            | Character source         |
| --------- | ------------------------------- | ------------------------ |
| `hsf2`    | Hyper Street Fighter II         | `references/hsf2.txt`    |
| `sfa3`    | Street Fighter Alpha 3          | `references/sfa3.txt`    |
| `sfiii3`  | Street Fighter III: 3rd Strike  | `references/sfiii3.txt`  |
| `kof98`   | The King of Fighters '98        | `references/kof98.txt`   |
| `kof2001` | The King of Fighters 2001       | `references/kof2001.txt` |
| `ssvsp`   | Samurai Shodown V Special       | `references/ssvsp.txt`   |

The last three are on the Neo Geo's four-button panel rather than the Street
Fighter six. The two King of Fighters entries have the smallest trainable share
of any game here (63% and 57%): KoF leans on close-range command throws and long
follow-up chains, neither of which the engine models.

Samurai Shodown V Special is on the same panel but means something different by
it — A and B are the weak and medium slash, A+B the strong one, C kicks and D is
the dodge. Its motions are plainer than KoF's, so 74% of the move list is
trainable.

Each game has its own `Ruleset` in
[`games/rulesets.py`](https://github.com/kism/motioninput-tui/blob/main/src/motioninput_tui/games/rulesets.py)
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
motioninput-tui --config path/to/config.json # use a different config file
```

### Input display

The first entry in the game list is not a game: it draws your panel and lights
it up as you press, with no moves and nothing to recognise. Its "characters"
are the button sets below, so pick the one your game uses. Directions are
cleaned exactly as they are in the trainer, so it is also the quickest way to
see what your keyboard is really sending.

```text
 ╭───╮ ╭───╮ ╭───╮    ╭─────╮ ╭─────╮ ╭─────╮
 │ ↖ │ │ ↑ │ │ ↗ │    │  LP │ │  MP │ │  HP │
 ╰───╯ ╰───╯ ╰───╯    │  u  │ │  i  │ │  o  │
 ╭───╮ ╭───╮ ╭───╮    ╰─────╯ ╰─────╯ ╰─────╯
 │ ← │ │ · │ │ → │    ╭─────╮ ╭─────╮ ╭─────╮
 ╰───╯ ╰───╯ ╰───╯    │  LK │ │  MK │ │  HK │
 ╭───╮ ╭───╮ ╭───╮    │  j  │ │  k  │ │  l  │
 │ ↙ │ │ ↓ │ │ ↘ │    ╰─────╯ ╰─────╯ ╰─────╯
 ╰───╯ ╰───╯ ╰───╯
```

### Picking what to train

The app opens on a full screen input picker: keyboard layout or gamepad, since
that decides how the trainer reads you rather than what you are training. Press
`enter` and the next screen has three panes, `tab` between them:

| Pane      | What it is                                               |
| --------- | -------------------------------------------------------- |
| Settings  | Your own options, which sit above whatever the game says |
| Game      | Which game's rules to judge your inputs by               |
| Character | Whose move list to train                                 |

`space` flips the highlighted setting; `enter` moves on from the game pane and
starts training from either of the others. `esc` goes back to the input picker.

`ctrl+b` in the trainer brings the same settings up over your session, so you
can change them without leaving it: `space` to flip one, `enter` or `esc` when
you are done. A change applies immediately; the input buffer is cleared with
it, since what was in it was read under the old rules.

### Move notation

`ctrl+n`, from the setup screen or the trainer, opens the second menu: how the
move list and the activation feed write a move's input. Pick a motion on the
left and a style on the right, where every row is drawn in the style it offers,
so you can see what your font makes of it before taking it.

| Motion          | Written as                                                          |
| --------------- | ------------------------------------------------------------------- |
| Directions      | `↓ ↘ →`, `D, DF, F`, `236`, `⬇️ ↘️ ➡️`, `2️⃣3️⃣6️⃣`                    |
| Quarter circles | spelled out, or `⮡ ⮠`, `⮩ ⮨`, `⮱ ⮰`, `⮑ ⮐`, `🔥 →`                  |
| Half circles    | spelled out, or `⋃ →`, `◡ →`, `🌙 →`                                |
| Dragon punches  | spelled out, or `𑪼 𑪽`, `𐰁 𐰀`, `龍 →`, `龙 →`, `竜 →`, `𓆈 →`, `🐉 →` |
| Full circles    | `360` `720`, or `⥁`, `⭮`, `🌀`                                      |
| Charges         | `[←] →`, or `⮀ ⮃`, `🔋 →`                                           |

`236` is the numpad, from a player on the left: `236 + P` is a fireball and
`623 + P` a dragon punch, which is how the notation is written everywhere else.

Every family also offers a nerd font style, directions included (the numpad in
boxes). Those glyphs live in the private use area, so they are empty boxes
without a patched font — which the preview will show you.

A motion nobody has a glyph for is spelled out in whatever directions are set
to, and a compound motion follows its parts: a super that is two quarter
circles reads `⮩ ×2` once quarter circles are curved arrows. Moves the engine
has no directional model of keep the reference guide's own wording.

The live input strip is deliberately not part of this. What you actually
pressed is always arrows, so there is one reading of the display that never
changes whatever else you pick.

### Settings

These are yours, not the games', so they apply whichever game is selected.

| Setting              | Default | Off                                    | On                                |
| -------------------- | ------- | -------------------------------------- | --------------------------------- |
| Relaxed half circles | on      | A half circle has to pass through down | `b,db,df,f` counts as one         |
| Neo Geo slant        | off     | A B C D straight across                | A B on the bottom row, C D above  |
| Loose buffer         | off     | Inputs are spent when a move comes out | One motion can feed several moves |

Relaxed half circles is on by default because of how a hitbox or a keyboard
actually plays: pressing forward while back is still held goes straight to
down-forward, so an ordinary half circle never touches straight down at all.
Turn it off to be made to hit the down. Loose buffer is the same rule
`--loose-buffer` controls, described under [spending inputs](#spending-inputs).

### Remembering your last session

The game, character, layout, settings, notation and buffer rule you last used
are saved to `~/.config/motioninput-tui/config.json` (or under
`$XDG_CONFIG_HOME` if set), so the pickers open where you left off and your
settings stick between runs.

Command line arguments win over what was saved, and `--no-loose-buffer` turns
the buffer rule back off. Naming a different `--game` on its own clears the
remembered character, since it belonged to another roster. If the file is
missing or damaged the defaults are used and a fresh one is written.

Key release support is _not_ remembered: it is probed per terminal on every
launch, so a saved value would disable exact tracking after switching terminal.

## Controls

Chosen on the first screen. Two keyboard layouts, plus a gamepad if the
`gamepad` extra is installed (`uv sync --extra gamepad`, or `--all-extras`).

| Layout   | Back / Down / Forward / Up | Attack row 1 | Attack row 2 |
| -------- | -------------------------- | ------------ | ------------ |
| Hitbox   | `a` `s` `d` `space`        | `u i o p`    | `j k l ;`    |
| Southpaw | `j` `k` `l` `space`        | `a s d f`    | `z x c v`    |
| Gamepad  | D-pad or left stick        | `X Y RB RT`  | `A B LB LT`  |

A layout is only _where_ the attacks are. What those positions mean is the
game's button set, laid onto them in order:

| Panel                 | Row 1    | Row 2    | On southpaw       |
| --------------------- | -------- | -------- | ----------------- |
| Street Fighter, 6     | LP MP HP | LK MK HK | `asd` `zxc`       |
| Mortal Kombat, 5      | HP BL HK | LP LK    | `asd` `zx`        |
| Neo Geo, 4            | A B C D  | A B C D  | `asdf` and `zxcv` |
| Neo Geo, arcade slant | C D      | A B      | `as` over `zx`    |
| Tekken, 4             | □ △      | ✕ ○      | `as` `zx`         |
| Eight button          | 1 2 3 4  | 5 6 7 8  | `asdf` `zxcv`     |

The Street Fighter games use the six, so that is what a layout carries unless
something else asks for another set. The Neo Geo is the one panel with two
arrangements in circulation, so which one you get is a setting: **Neo Geo
slant** puts A B on the bottom row with C D above, instead of A B C D straight
across both rows.

The gamepad attack buttons start on the Xbox-style default above; the triggers
(`LT` `RT`) are free to bind to as well. Highlight the gamepad row in the input
picker (it names your connected pad) and press `b` to remap them; the map is
remembered in the config. Movement stays on the d-pad and left stick. Buttons
are read through SDL's controller database, so any recognised pad works
regardless of how its firmware numbers them. A pad reports button releases, so
holds are always exact with one plugged in.

In the trainer: `esc` goes back to the setup screen with the character list
focused, ready to pick someone else. `tab` equips the next Super Art in 3rd
Strike, `ctrl+r` clears the buffer, `ctrl+l` toggles the move list, `ctrl+b`
opens the settings, `ctrl+n` the move notation, and `ctrl+q` or two presses of
`ctrl+c` quit.

## Super Arts

In 3rd Strike you pick one Super Art of three before a match, and most of the
roster has two or three of them on the very same `qcf, qcf + P`. So the trainer
equips one too: `tab` cycles I, II and III, the banner says which is live, and
the move list marks it with `▸` and dims the other two. Only the equipped one
can come out, which is the only way to tell Sean's Hadou Burst, Shouryuu Cannon
and Hyper Tornado apart.

Some Super Arts want you to keep tapping after the motion — Sean's Shouryuu
Cannon is `qcf, qcf + P, tap P rapidly`. Those need the taps as well as the
motion, so on SA II the two quarter circles alone will not give you the move.

No other game here works this way; every super is always available, and `tab`
does nothing.

## Spending inputs

When a special comes out, the games clear the command buffer so the inputs that
produced it cannot go on to feed another move. Without that, two fireballs in a
row would read as the double quarter circle of a super. Normals and throws do
not clear it, matching the games.

Steps of a motion also have to be close together, not merely finish inside a
time limit. The forward you are still holding after a fireball is genuinely
still held, so without a per-step limit a later down, down-forward would turn
it into a dragon punch.

`--loose-buffer`, or the loose buffer setting (`ctrl+b` in the trainer), turns
both off. Inputs are then reused freely and one motion can light up several
moves at once. No game behaves that way, but it is a useful way to see
everything your inputs contain.

## Terminal choice matters

Motions are judged on wall clock timing, so a terminal that is slow to paint
makes clean inputs read as late. The app identifies your terminal on launch and
warns if it is likely to get in the way.

Comfortable: alacritty, ghostty, foot, kitty, wezterm, contour, rio, st.
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

Supported by Ghostty, Alacritty, WezTerm, kitty, foot, Contour, Rio. Check
yours with:

```bash
motioninput-tui --check-terminal
```

Pass `--no-key-release` to turn it off and use the fallback instead.

### Inferred holds (fallback)

Without release reporting, a held direction has to be deduced from the
auto-repeat stream. A press counts as held for a short window and auto-repeat
keeps it alive beyond that. If your operating system waits a long time before
it starts repeating, that quiet gap is invisible and holds read as taps, which
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

## Special thanks

Kao Megura / Chris MacDonald —
<https://web.archive.org/web/20040520095719/http://cgfm2.emuviews.com/>

```{toctree}
:hidden:
:maxdepth: 1

adding-a-game
development
```
