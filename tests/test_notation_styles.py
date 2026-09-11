"""Writing a move's input out in the notation the player picked.

The rosters are the real test data here: every motion kind the guides produce
has to come out as something a person can read, in every style on offer.
"""

import pytest

from motioninput_tui.engine.motions import MotionKind, MotionSpec
from motioninput_tui.engine.notation import ANY_KICK, ANY_PUNCH, Direction
from motioninput_tui.engine.recognizer import NOT_MOTIONS
from motioninput_tui.games.loader import load_game
from motioninput_tui.games.models import Move
from motioninput_tui.notation_styles import DEFAULT, MOTION_NAMES, MOTION_SHORTHANDS, STYLES, Family, Notation

GAMES = ("hsf2", "sfa3", "sfiii3", "kof98", "lb2")
"""Two SNK rosters as well, since the rolls their supers are written on do not
appear in any Street Fighter move list."""


def moves_by_kind() -> dict[MotionKind, Move]:
    """One real move per motion kind, out of every roster."""
    found: dict[MotionKind, Move] = {}
    for key in GAMES:
        for character in load_game(key).characters:
            for move in character.moves:
                if move.motion is not None:
                    found.setdefault(move.motion.kind, move)
    return found


ALL_STYLES = [(family, style) for family, styles in STYLES.items() for style in styles]


@pytest.mark.parametrize(("family", "style"), ALL_STYLES, ids=lambda value: getattr(value, "key", str(value)))
def test_every_style_writes_every_motion(family: Family, style) -> None:
    notation = DEFAULT.with_style(family, style)
    for kind, move in moves_by_kind().items():
        written = notation.write_move(move)
        assert written.strip(), f"{kind} came out blank"


@pytest.mark.parametrize(("family", "style"), ALL_STYLES, ids=lambda value: getattr(value, "key", str(value)))
def test_every_style_previews_itself(family: Family, style) -> None:
    assert DEFAULT.preview(family, style).strip()


def test_arrows_are_the_default() -> None:
    assert DEFAULT.write(MotionSpec(kind=MotionKind.QCF, buttons=ANY_PUNCH)) == "↓ ↘ → + P"


def test_letters_write_the_directions_out() -> None:
    letters = Notation({"directions": "letters"})
    assert letters.write(MotionSpec(kind=MotionKind.QCF, buttons=ANY_PUNCH)) == "D, DF, F + P"


def test_numpad_writes_the_conventional_numbers() -> None:
    """236 and 623 are how the notation is written everywhere else."""
    numpad = Notation({"directions": "numpad"})
    assert numpad.write(MotionSpec(kind=MotionKind.QCF, buttons=ANY_PUNCH)) == "236 + P"
    assert numpad.write(MotionSpec(kind=MotionKind.DP, buttons=ANY_PUNCH)) == "623 + P"
    assert numpad.write(MotionSpec(kind=MotionKind.HCF, buttons=ANY_PUNCH)) == "41236 + P"
    assert numpad.write(MotionSpec(kind=MotionKind.CHARGE_BF, buttons=ANY_KICK)) == "[4] 6 + K"


def test_the_numpad_digits_are_the_directions_own_numbers() -> None:
    """Numpad notation is the enum, so the two can never drift apart."""
    numpad = Notation({"directions": "numpad"})
    for direction in Direction:
        assert numpad.directions((direction,)) == str(int(direction))


def test_emoji_arrows_replace_the_plain_ones() -> None:
    emoji = Notation({"directions": "emoji"})
    assert emoji.write(MotionSpec(kind=MotionKind.QCF, buttons=ANY_PUNCH)) == "⬇️ ↘️ ➡️ + P"


def test_emoji_keycaps_write_the_numpad() -> None:
    keycaps = Notation({"directions": "keycaps"})
    assert keycaps.write(MotionSpec(kind=MotionKind.QCF, buttons=ANY_PUNCH)) == "2️⃣3️⃣6️⃣ + P"


def test_an_emoji_style_names_the_move_it_stands_for() -> None:
    emoji = Notation({"quarter": "emoji", "dragon": "emoji"})
    assert emoji.write(MotionSpec(kind=MotionKind.QCF, buttons=ANY_PUNCH)) == "🔥→ + P"
    assert emoji.write(MotionSpec(kind=MotionKind.DP, buttons=ANY_PUNCH)) == "🐉→ + P"


def test_style_keys_are_unique_within_a_family() -> None:
    """The config stores a key per family, so a duplicate would be unreachable."""
    for family, styles in STYLES.items():
        keys = [style.key for style in styles]
        assert len(keys) == len(set(keys)), f"{family} has a repeated style key"


def test_a_glyph_replaces_the_directions() -> None:
    elbow = Notation({"quarter": "elbow"})
    assert elbow.write(MotionSpec(kind=MotionKind.QCF, buttons=ANY_PUNCH)) == "⬏ + P"


def test_632_and_412_are_set_apart_from_the_quarter_circles() -> None:
    """The same quarter of the circle run the other way round, which reads as a different motion."""
    down = Notation({"quarter_down": "quadrant"})
    assert down.write(MotionSpec(kind=MotionKind.F_DF_D, buttons=ANY_KICK)) == "◶↓ + K"
    assert down.write(MotionSpec(kind=MotionKind.B_DB_D, buttons=ANY_KICK)) == "◵↓ + K"
    assert down.write(MotionSpec(kind=MotionKind.QCF, buttons=ANY_KICK)) == "↓ ↘ → + K"
    quarters = Notation({"quarter": "quadrant"})
    assert quarters.write(MotionSpec(kind=MotionKind.F_DF_D, buttons=ANY_KICK)) == "→ ↘ ↓ + K"


def test_a_compound_motion_follows_the_styles_of_its_parts() -> None:
    """A super that is a quarter circle and a dragon punch uses both choices."""
    picked = Notation({"quarter": "elbow", "dragon": "kanji"})
    assert picked.write(MotionSpec(kind=MotionKind.QCF_DP, buttons=ANY_PUNCH)) == "⬏  龍→ + P"


def test_the_snk_rolls_are_written_as_the_parts_they_are_made_of() -> None:
    """Neither is a motion of its own to look at: one is a quarter circle back
    that turns around, the other a forward tap before a half circle."""
    assert DEFAULT.write(MotionSpec(kind=MotionKind.QCB_DB_F, buttons=ANY_PUNCH)) == "↓ ↙ ←  ↙  → + P"
    assert DEFAULT.write(MotionSpec(kind=MotionKind.F_HCF, buttons=ANY_PUNCH)) == "→  ← ↙ ↓ ↘ → + P"
    numpad = Notation({"directions": "numpad"})
    assert numpad.write(MotionSpec(kind=MotionKind.QCB_DB_F, buttons=ANY_PUNCH)) == "214  1  6 + P"
    assert numpad.write(MotionSpec(kind=MotionKind.F_HCF, buttons=ANY_PUNCH)) == "6  41236 + P"


def test_a_motion_done_twice_is_marked_rather_than_repeated() -> None:
    assert DEFAULT.write(MotionSpec(kind=MotionKind.QCF_X2, buttons=ANY_KICK)) == "↓ ↘ → ×2 + K"


def test_a_charge_shows_what_is_held() -> None:
    assert DEFAULT.write(MotionSpec(kind=MotionKind.CHARGE_BF, buttons=ANY_KICK)) == "[←] → + K"


def test_a_follow_through_is_written_after_the_motion() -> None:
    rapid = MotionSpec(kind=MotionKind.QCF_X2, buttons=ANY_PUNCH, mash=3)
    assert DEFAULT.write(rapid) == "↓ ↘ → ×2 + P, mash P"
    taps = MotionSpec(kind=MotionKind.DP, buttons=ANY_KICK, mash=3, mash_rhythm=True, mash_button="P")
    assert DEFAULT.write(taps) == "→ ↓ ↘ + K, tap P×3"


def test_a_style_with_no_glyph_for_a_kind_spells_it_out() -> None:
    """Paired arrows have nothing for the down-back charge, so it stays written out."""
    paired = Notation({"charge": "paired"})
    assert paired.write(MotionSpec(kind=MotionKind.CHARGE_DB_UF, buttons=ANY_KICK)) == "[↙] ↘ ↙ ↗ + K"


def test_a_hold_is_written_as_the_direction_held() -> None:
    spec = MotionSpec(kind=MotionKind.HOLD, buttons=ANY_PUNCH, hold=Direction.FORWARD)
    assert DEFAULT.write(spec) == "→ + P"


def test_an_unmodelled_move_keeps_the_guides_own_words() -> None:
    """There is no motion to draw, and the wording is all the player has."""
    move = Move(name="Hop", command="Back or Forward + press all Kicks (ST only)", motion=None)
    assert DEFAULT.write_move(move) == "Back or Forward + press all Kicks"


def test_spelled_out_keeps_the_directions_and_drops_the_glyphs() -> None:
    """The input display's ctrl+l: the same arrows or numbers, and no shorthand for whole motions."""
    picked = Notation({"directions": "numpad", "quarter": "elbow", "mark": "emoji"})
    assert picked.write(MotionSpec(kind=MotionKind.QCF, buttons=ANY_PUNCH)) == "⬏ + P"
    spelled = picked.spelled_out()
    assert spelled.write(MotionSpec(kind=MotionKind.QCF, buttons=ANY_PUNCH)) == "236 + P"
    assert spelled.mark == "✅"


def test_every_motion_has_a_name() -> None:
    """The input display lists each one by name; throws, holds and mashes are not motions."""
    assert MOTION_NAMES.keys() == set(MotionKind) - NOT_MOTIONS
    assert MOTION_SHORTHANDS.keys() == MOTION_NAMES.keys()


def test_the_button_mark_is_a_bang_unless_another_is_picked() -> None:
    """What the trainer's history puts over a throw or a counted tap."""
    assert DEFAULT.mark == "!"
    assert Notation({"mark": "emoji"}).mark == "✅"
    assert Notation({"mark": "gone"}).mark == "!"


def test_a_style_that_is_gone_falls_back_rather_than_failing() -> None:
    stale = Notation({"quarter": "sharpie", "nonsense": "whatever"})
    assert stale.write(MotionSpec(kind=MotionKind.QCF, buttons=ANY_PUNCH)) == "↓ ↘ → + P"


def test_previewing_a_style_leaves_the_other_families_alone() -> None:
    """Only the family being previewed changes, so a row shows one decision."""
    picked = Notation({"dragon": "kanji"})
    quadrant = next(style for style in STYLES[Family.QUARTER] if style.key == "quadrant")
    assert picked.preview(Family.QUARTER, quadrant) == "◶→   ◵←"
    assert picked.write(MotionSpec(kind=MotionKind.DP, buttons=ANY_PUNCH)) == "龍→ + P"
