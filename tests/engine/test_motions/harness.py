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

# Hitbox: a is back, s is down, d is forward, space is up. Attacks on u i o / j k l.
BACK, DOWN, FORWARD, UP = "a", "s", "d", "space"
LP, MP, HP = "u", "i", "o"
LK, MK, HK = "j", "k", "l"

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
) -> Attempt:
    """Run a script against one character, on a clock the test controls.

    ``ruleset`` stands in for the game's own rules, which is how the player's
    settings reach the engine; without one the game's are used as they stand.
    """
    game = load_game(game_key)
    if ruleset is not None:
        game = replace(game, ruleset=ruleset)
    # The hitbox keys keep their positions; a non-Street-Fighter game relabels
    # what those positions mean (the Neo Geo's u/o become A/C), exactly as the
    # app does when it lays the game's panel onto the layout.
    layout = with_buttons(HITBOX, game.buttons)
    session = TrainingSession(game, game.character(character_key), layout, exact_input=exact_input)
    now = 0
    for event in script:
        while now < event.at_ms:
            now = min(now + TICK_MS, event.at_ms)
            session.tick(now)
        if event.down:
            session.press(event.key, event.at_ms)
        else:
            session.release(event.key, event.at_ms)
    for _ in range(SETTLE_TICKS):
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

# Back, then add down, then add forward. Pressing forward while back is still
# held gives down-forward straight away, so a plain down never appears. This is
# an ordinary hitbox half circle, and whether it counts as one is the player's
# "relaxed half circles" setting rather than anything the games disagree on.
HALF_CIRCLE_SKIPPING_DOWN_MK: Script = [
    press(BACK, 0),
    press(DOWN, 60),
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
