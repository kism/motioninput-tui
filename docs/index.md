# motioninput-tui

A terminal trainer for fighting game motion inputs. Pick a game and a character,
press inputs, and watch which moves come out. The point is that the same input
does different things in different games: hold down and double tap forward in
3rd Strike and you get a dragon punch, do it in Super Turbo or Alpha 3 and you
get nothing.

See [Adding a game](adding-a-game.md) to add another title, or
[Development](development.md) for the architecture and the check/test setup.

## Games

Hyper Street Fighter II, Street Fighter Alpha 3, 3rd Strike, Ultra Street
Fighter IV, The King of Fighters '98 and 2001, Samurai Shodown II and V
Special, and The Last Blade 2. The picker lists them with a note on what makes
each one's input handling different.

Each has its own `Ruleset` describing how forgiving it is — motion windows,
whether diagonals can be skipped, charge times, whether the dragon punch
shortcut exists. 3rd Strike's figures come from a decompilation of the game
rather than from feel; see [Third Strike, from the decompiled
game](sfiii3-from-the-decomp.md).

Not every listed move is trainable. The Street Fighter rosters run 79-89%; the
SNK ones are lower — 52% for Samurai Shodown II — because those guides lean on
command throws written "b or f + button", which say nothing about which way to
hold, and on long follow-up chains. The rest still appear in the move list,
struck through. The five SNK games are on the Neo Geo's four-button panel, and
each means something different by it, which the game's own note explains when
you highlight it.

## Run

### Install

Needs Python 3.14 or newer.

```bash
uv tool install motioninput-tui      # pipx install motioninput-tui
```

That puts `motioninput-tui` on your PATH, along with `motioninput-tui-probe`
for dumping what a gamepad is actually sending. To try it without installing,
`uv tool run motioninput-tui` (or `pipx run motioninput-tui`) does the same in
one shot.

uv will fetch Python 3.14 itself if you do not have it. pipx builds its
virtualenv from an interpreter it can already find, so on a system whose
default Python is older it wants pointing at one:
`pipx install --python 3.14 motioninput-tui`.

Upgrade with `uv tool upgrade motioninput-tui` (`pipx upgrade`), remove with
`uv tool uninstall motioninput-tui` (`pipx uninstall`).

### From a clone

```bash
uv venv
source .venv/bin/activate
uv sync --all-groups # Omit --all-groups for prod
```

See [development](development.md) for the rest of the developer setup.

### Running the app

```bash
motioninput-tui                              # this is the one you want
motioninput-tui --list                       # games and characters, then exit
motioninput-tui --check-terminal             # terminal speed and key release support
motioninput-tui --config path/to/config.json # use a different config file
```

That is the whole command line. What to train — the game, the character, the
layout, the settings — is not on it: you pick those in the app and it remembers
them, so there is one place they live rather than two that have to agree.

### Input display

Every game's character list opens with **Input display**: the game's panel, lit
up as you press, with every motion the game has drawn over your input history
as you make it, whoever's move it would be. A motion goes green when a button
brings it out and dim when it lapses. Directions are cleaned exactly as they
are in the trainer, so it is the quickest way to see what your keyboard is
really sending.

### Picking what to train

The app opens on an input picker — keyboard layout or gamepad — because that
decides how the trainer reads you rather than what you are training. The next
screen has three panes: your settings, the game whose rules judge you, and the
character whose move list you want.

`ctrl+b` brings the settings up again during a session. A change applies
immediately and clears the input buffer with it, since what was in it was read
under the old rules.

### Move notation

`ctrl+n` chooses how a move's input is written — arrows, letters, numpad, or
one of several glyph sets. Every row in that menu is drawn in the style it
offers, so it doubles as a test of what your font can render; the nerd font
styles in particular are empty boxes without a patched font.

`236` is the numpad, counted from a player on the left: `236 + P` is a fireball
and `623 + P` a dragon punch.

A motion nobody has a glyph for is spelled out in whatever directions are set
to, and a compound motion follows its parts, so a super that is two quarter
circles reads `⮩ ×2` once quarter circles are curved arrows. Moves the engine
has no directional model of keep the reference guide's own wording.

The live input strip is deliberately not part of this: what you actually
pressed is always arrows, so one reading of the display never changes whatever
else you pick.

### Settings

Three toggles, in the setup screen's first pane and under `ctrl+b`, which
describe themselves as you highlight them. They are yours rather than the
games', so they apply whichever game is selected.

Relaxed half circles is the one worth knowing about, and it is on by default
because of how a hitbox or a keyboard actually plays: pressing forward while
back is still held goes straight to down-forward, so an ordinary half circle
never touches straight down at all. Turn it off to be made to hit the down.
Loose buffer is the rule described under [spending inputs](#spending-inputs).

### Remembering your last session

The game, character, layout, settings, notation and buffer rule you last used
are saved to `~/.config/motioninput-tui/config.json` (or under
`$XDG_CONFIG_HOME` if set), so the pickers open where you left off and your
settings stick between runs. The character is remembered per game, so switching
game switches to whoever you were last training on it.

Nothing on the command line overrides any of it — `--config` only chooses which
file to read. If that file is missing or damaged the defaults are used and a
fresh one is written.

Key release support is _not_ remembered: it is probed per terminal on every
launch, so a saved value would disable exact tracking after switching terminal.

## Controls

Chosen on the first screen: two keyboard presets, a rebindable one, and a
gamepad if one is plugged in. Press `b` on the custom keyboard row or the
gamepad row to remap it; either map is remembered in the config. Gamepad
movement stays on the d-pad and left stick and is not rebindable.

A layout is only *where* the attacks are — six positions, three to a row. What
those positions mean is the game's button set, laid onto them in order, which
is why a game with a different panel is a table entry rather than a new layout.

That fits the Street Fighter six, but not the Neo Geo.
`A B C D` across a three-key row leaves **D** with nowhere to go, so on a
keyboard the Neo Geo's fourth button cannot be pressed at all. Turning on the
**Neo Geo slant** setting fixes it — `C D` on the top row, `A B` on the bottom
— and a gamepad has all four either way. Worth doing if you train KoF or
Samurai Shodown on a keyboard: 36 trainable moves across those rosters ask for
D alone.

Pad buttons are read through SDL's controller database, so any recognised pad
works however its firmware numbers them, and a pad reports releases, so holds
are always exact with one plugged in.

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
The super's activation cinematic runs first and the game reads nothing while it
does, so the taps have to wait it out; the prompt says `wait...` until they will
count.

Ultra SF4 works the same way with its two Ultra Combos, which you also pick
before a match: `tab` cycles I and II, and it is what separates Ryu's Metsu
Hadouken from his Metsu Shoryuken. In every other game here each super is always
available and `tab` does nothing.

## Spending inputs

When a special comes out, the games clear the command buffer so the inputs that
produced it cannot go on to feed another move. Without that, two fireballs in a
row would read as the double quarter circle of a super. Normals and throws do
not clear it, matching the games.

Steps of a motion also have to be close together, not merely finish inside a
time limit. The forward you are still holding after a fireball is genuinely
still held, so without a per-step limit a later down, down-forward would turn
it into a dragon punch.

The loose buffer setting turns both off. Inputs are then reused freely and one
motion can light up several moves at once. No game behaves that way, but it is
a useful way to see everything your inputs contain.

## Your terminal matters

Two things about the terminal decide how accurately the trainer can read you,
and `motioninput-tui --check-terminal` reports both, names the terminals that
do the job well, and says what yours is doing.

**Speed.** Motions are judged on wall clock timing, so a terminal slow to paint
makes clean inputs read as late. Running under tmux or screen, or over SSH,
adds latency on top of whatever you are using.

**Key releases.** A plain terminal only ever says a key went *down*, and
knowing when the player let go of down is the difference between a fireball and
a dragon punch. The kitty keyboard protocol adds an event type to each key
report, so releases arrive too; where it is available holds are tracked exactly
and your keyboard repeat settings stop mattering.

Without it a hold has to be deduced from the auto-repeat stream, which mostly
hurts charge moves: if your operating system waits a long time before it starts
repeating, that quiet gap is invisible and holds read as taps. The trainer
measures the delay as you play and widens its window to match, but it is better
fixed at the source:

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

Move list guides by Kao Megura / Chris MacDonald
(<https://web.archive.org/web/20040520095719/http://cgfm2.emuviews.com/>) for
every game except Hyper Street Fighter II, whose guide is by x_MJ_x.

```{toctree}
:hidden:
:maxdepth: 1

adding-a-game
development
manual-testing
sfiii3-from-the-decomp
```
