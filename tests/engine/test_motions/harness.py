"""Shared machinery for the per game, per character motion tests.

Every test file sits at ``test_motions/<game>/test_<character>.py``, so a file
is the record of what one character does in one game, checked against how the
real game behaves. The ``play`` fixture in ``conftest.py`` reads the game and
the character out of that path, which is why the tests themselves never name
them.

Scripts are run through the real input source at the key level, so SOCD
cleaning and the direction states it produces are covered as well as the
matchers. ``exact_input=True`` means key releases are reported, as they are in a
terminal speaking the kitty keyboard protocol, so no auto-repeat has to be
simulated. A test of the inferred path has to opt out and send the repeat
stream itself.
"""

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from motioninput_tui.controls.layouts import HITBOX, with_buttons
from motioninput_tui.engine.session import TrainingSession
from motioninput_tui.games.loader import load_game

if TYPE_CHECKING:
    from motioninput_tui.engine.ruleset import Ruleset

# Hitbox: a is back, s is down, d is forward, space is up.
# Attacks are four to a row, u i o p over j k l ;, and the game's panel decides
# what those positions mean.
BACK, DOWN, FORWARD, UP = "a", "s", "d", "space"
LP, MP, HP = "u", "i", "o"
LK, MK, HK = "j", "k", "l"

# The same top row under the Neo Geo's names, for the SNK games. Worth using
# by name where the panel is not punches and kicks: in Samurai Shodown A and B
# are slashes, C is the kick and D the dodge, so calling C "HP" reads as a lie.
NEO_A, NEO_B, NEO_C, NEO_D = "u", "i", "o", "p"

TICK_MS = 8
"""How finely time is advanced between events, so hold expiry runs as it does live."""

SETTLE_TICKS = 20
"""Ticks run after the last event, giving late activations a chance to appear."""


@dataclass(frozen=True, slots=True)
class Event:
    """One key going down or coming up at a known moment."""

    key: str
    at_ms: int
    down: bool


type Script = list[Event]


def press(key: str, at_ms: int) -> Event:
    """A key going down."""
    return Event(key=key, at_ms=at_ms, down=True)


def release(key: str, at_ms: int) -> Event:
    """A key coming up."""
    return Event(key=key, at_ms=at_ms, down=False)


def taps(key: str, start_ms: int, count: int, *, gap_ms: int = 180) -> Script:
    """``count`` presses of one key, ``gap_ms`` apart, for a follow-through."""
    script: Script = []
    for index in range(count):
        at = start_ms + index * gap_ms
        script += [press(key, at), release(key, at + gap_ms // 3)]
    return script


@dataclass(frozen=True, slots=True)
class Attempt:
    """What the trainer made of a script."""

    session: TrainingSession
    directions: str
    """The input strip as arrows, e.g. ``"← ↙ ↓ ↘ →"``."""
    moves: list[str]
    """Names of the moves that came out, oldest first."""


def play_as(
    game_key: str,
    character_key: str,
    script: Script,
    *,
    exact_input: bool = True,
    ruleset: Ruleset | None = None,
    super_art: str | None = None,
    settle_ms: int = 0,
) -> Attempt:
    """Run a script against one character, on a clock the test controls.

    ``ruleset`` stands in for the game's own rules, which is how the player's
    settings reach the engine; without one the game's are used as they stand.
    ``super_art`` equips one of 3rd Strike's three, as ``tab`` does in the
    trainer; without one the session starts on the first, as it does live.
    ``settle_ms`` keeps ticking that long past the last event, for a follow-up
    window that has to be allowed to expire.
    """
    game = load_game(game_key)
    if ruleset is not None:
        game = replace(game, ruleset=ruleset)
    # The hitbox keys keep their positions; a non-Street-Fighter game relabels
    # what those positions mean (the Neo Geo's u/o become A/C), exactly as the
    # app does when it lays the game's panel onto the layout.
    layout = with_buttons(HITBOX, game.buttons)
    session = TrainingSession(game, game.character(character_key), layout, exact_input=exact_input)
    if super_art is not None:
        session.select_super_art(super_art)
    now = 0
    for event in script:
        while now < event.at_ms:
            now = min(now + TICK_MS, event.at_ms)
            session.tick(now)
        if event.down:
            session.press(event.key, event.at_ms)
        else:
            session.release(event.key, event.at_ms)
    for _ in range(SETTLE_TICKS + settle_ms // TICK_MS):
        now += TICK_MS
        session.tick(now)
    return Attempt(
        session=session,
        directions=" ".join(entry.direction.glyph for entry in session.entries),
        moves=[activation.name for activation in session.activations][::-1],
    )


def target_from_path(path_parts: tuple[str, ...]) -> tuple[str, str]:
    """The game and character a test file's location stands for.

    The directory is the game key and the file name is the character key, with
    underscores standing in for the hyphens the rosters use, since a module
    cannot be called ``test_chun-li``.
    """
    directory, file_name = path_parts[-2], path_parts[-1]
    character = file_name.removeprefix("test_").removesuffix(".py").replace("_", "-")
    return directory, character


# Canonical inputs. Sharing the exact script is the point for these: the same
# keys at the same moments give a dragon punch in 3rd Strike and nothing at all
# in Alpha 3 or Super Turbo, which is the difference the trainer exists to show.

DOWN_DOUBLE_TAP_FORWARD_HP: Script = [
    press(DOWN, 0),
    press(FORWARD, 80),
    release(FORWARD, 150),
    press(FORWARD, 230),
    press(HP, 270),
]

QUARTER_CIRCLE_FORWARD_HP: Script = [
    press(DOWN, 0),
    press(FORWARD, 70),
    release(DOWN, 110),
    press(HP, 150),
]

# Back, then add down, then swap back for forward in one go, so down-forward
# follows down-back and a plain down never appears. (Adding forward with back
# still held would give down: a keyboard's SOCD is neutral.) 3rd Strike reads a
# half circle at three points, so any down will do there; elsewhere this misses.
HALF_CIRCLE_SKIPPING_DOWN_MK: Script = [
    press(BACK, 0),
    press(DOWN, 60),
    release(BACK, 120),
    press(FORWARD, 120),
    release(DOWN, 180),
    release(BACK, 185),
    press(MK, 220),
]

# The same motion rolled cleanly through every direction, down included.
HALF_CIRCLE_THROUGH_DOWN_MK: Script = [
    press(BACK, 0),
    press(DOWN, 60),
    release(BACK, 100),
    press(FORWARD, 140),
    release(DOWN, 180),
    press(MK, 220),
]


# KoF's compound supers, where the two halves share the direction they meet on:
# a qcf~hcb rolls through d,df,f,df,d,db,b, and the forward the quarter circle
# ends on is the one the half circle starts from. The guide writing it
# ``qcf,hcb`` is shorthand, not an instruction to let go of forward and press it
# again - doing that would mean passing through neutral mid-motion.
QUARTER_FORWARD_INTO_HALF_BACK_HP: Script = [
    press(DOWN, 0),  # d
    press(FORWARD, 45),  # df
    release(DOWN, 90),  # f
    press(DOWN, 135),  # df
    release(FORWARD, 180),  # d
    press(BACK, 225),  # db
    release(DOWN, 270),  # b
    press(HP, 310),
]

QUARTER_BACK_INTO_HALF_FORWARD_HP: Script = [
    press(DOWN, 0),  # d
    press(BACK, 45),  # db
    release(DOWN, 90),  # b
    press(DOWN, 135),  # db
    release(BACK, 180),  # d
    press(FORWARD, 225),  # df
    release(DOWN, 270),  # f
    press(HP, 310),
]

# A half circle back with a forward on the end. Here the last forward is a real
# second press, with back let go as it goes down: on the keyboard's neutral
# SOCD, forward with back still held would be neutral.
HALF_CIRCLE_BACK_FORWARD_HP: Script = [
    press(FORWARD, 0),  # f
    press(DOWN, 40),  # df
    release(FORWARD, 80),  # d
    press(BACK, 120),  # db
    release(DOWN, 160),  # b
    release(BACK, 200),
    press(FORWARD, 200),  # f
    press(HP, 240),
]


# The two SNK rolls, neither of which Street Fighter has any move on.
#
# `d,db,b,db,f` is Terry's Power Geyser: a quarter circle back that turns
# around on the down-back and carries on to forward. Swapping back for forward
# there while down is still held gives a down-forward on the way, which is the
# one junk state between steps every ruleset here allows.
QUARTER_BACK_ROLLED_TO_FORWARD_HP: Script = [
    press(DOWN, 0),  # d
    press(BACK, 40),  # db
    release(DOWN, 80),  # b
    press(DOWN, 120),  # db
    release(BACK, 160),
    press(FORWARD, 160),  # df
    release(DOWN, 200),  # f
    press(HP, 240),
]

# `f,b,db,d,df,f` is Ryo's Haoh Shou Ko Ken: a forward tap, then a half circle
# forward. Forward is let go as back goes down, so this roll is clean from end
# to end - and dropping its first two events leaves exactly the plain half
# circle the move has to be told apart from.
FORWARD_INTO_HALF_CIRCLE_FORWARD_HP: Script = [
    press(FORWARD, 0),  # f
    release(FORWARD, 40),
    press(BACK, 40),  # b
    press(DOWN, 80),  # db
    release(BACK, 120),  # d
    press(FORWARD, 160),  # df
    release(DOWN, 200),  # f
    press(HP, 240),
]
