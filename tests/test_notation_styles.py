"""Writing a move's input out in the notation the player picked.

The rosters are the real test data here: every motion kind the guides produce
has to come out as something a person can read, in every style on offer.
"""

from __future__ import annotations

import pytest

from motioninput_tui.engine.motions import MotionKind, MotionSpec
from motioninput_tui.engine.notation import ANY_KICK, ANY_PUNCH, Direction
from motioninput_tui.games.loader import load_game
from motioninput_tui.games.models import Move
from motioninput_tui.notation_styles import DEFAULT, STYLES, Family, Notation

GAMES = ("hsf2", "sfa3", "sfiii3")


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


def test_a_glyph_replaces_the_directions() -> None:
    curved = Notation({"quarter": "curved"})
    assert curved.write(MotionSpec(kind=MotionKind.QCF, buttons=ANY_PUNCH)) == "⮩ + P"


def test_a_compound_motion_follows_the_styles_of_its_parts() -> None:
    """A super that is a quarter circle and a dragon punch uses both choices."""
    picked = Notation({"quarter": "curved", "dragon": "kanji"})
    assert picked.write(MotionSpec(kind=MotionKind.QCF_DP, buttons=ANY_PUNCH)) == "⮩  龍 → + P"


def test_a_motion_done_twice_is_marked_rather_than_repeated() -> None:
    assert DEFAULT.write(MotionSpec(kind=MotionKind.QCF_X2, buttons=ANY_KICK)) == "↓ ↘ → ×2 + K"


def test_a_charge_shows_what_is_held() -> None:
    assert DEFAULT.write(MotionSpec(kind=MotionKind.CHARGE_BF, buttons=ANY_KICK)) == "[←] → + K"


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


def test_a_style_that_is_gone_falls_back_rather_than_failing() -> None:
    stale = Notation({"quarter": "sharpie", "nonsense": "whatever"})
    assert stale.write(MotionSpec(kind=MotionKind.QCF, buttons=ANY_PUNCH)) == "↓ ↘ → + P"


def test_previewing_a_style_leaves_the_other_families_alone() -> None:
    """Only the family being previewed changes, so a row shows one decision."""
    picked = Notation({"dragon": "kanji"})
    quarter = STYLES[Family.QUARTER][1]
    assert picked.preview(Family.QUARTER, quarter) == "⮡   ⮠"
    assert picked.write(MotionSpec(kind=MotionKind.DP, buttons=ANY_PUNCH)) == "龍 → + P"
