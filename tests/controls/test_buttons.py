"""Laying a game's button set onto a layout's attack keys.

The arrangements are written down here in the keys they land on, which is how
they were specified and the only way to see at a glance that a panel is right.
"""

import pytest

from motioninput_tui.controls import buttons as sets
from motioninput_tui.controls.layouts import GAMEPAD, HITBOX, SOUTHPAW, with_buttons

SOUTHPAW_PANELS = [
    (sets.STREET_FIGHTER, {"a": "LP", "s": "MP", "d": "HP", "z": "LK", "x": "MK", "c": "HK"}),
    (sets.MORTAL_KOMBAT, {"a": "HP", "s": "BL", "d": "HK", "z": "LP", "x": "LK"}),
    (sets.NEO_GEO, {"a": "A", "s": "B", "d": "C", "f": "D", "z": "A", "x": "B", "c": "C", "v": "D"}),
    (sets.NEO_GEO_SLANT, {"a": "C", "s": "D", "z": "A", "x": "B"}),
    (sets.TEKKEN, {"a": "□", "s": "△", "z": "✕", "x": "○"}),
    (sets.EIGHT_BUTTON, {"a": "1", "s": "2", "d": "3", "f": "4", "z": "5", "x": "6", "c": "7", "v": "8"}),
]


@pytest.mark.parametrize(("button_set", "expected"), SOUTHPAW_PANELS, ids=lambda value: getattr(value, "key", ""))
def test_a_set_lands_on_the_keys_it_was_specified_in(button_set: sets.ButtonSet, expected: dict[str, str]) -> None:
    layout = with_buttons(SOUTHPAW, button_set)
    assert {key: button.value for key, button in layout.attacks.items()} == expected


def test_the_same_set_follows_the_layout_it_is_laid_on() -> None:
    """A panel is positions, so it moves with the hand the layout puts it under."""
    hitbox = with_buttons(HITBOX, sets.TEKKEN)
    assert {key: button.value for key, button in hitbox.attacks.items()} == {
        "u": "□",
        "i": "△",
        "j": "✕",
        "k": "○",
    }


def test_a_pad_gets_the_same_set_on_its_own_positions() -> None:
    layout = with_buttons(GAMEPAD, sets.NEO_GEO)
    assert layout.attacks["pad:2"] is sets.Button.A
    assert layout.attacks["pad:7"] is sets.Button.D
    assert layout.attacks["pad:0"] is sets.Button.A  # the second row, as on a stick


def test_the_neo_geo_binds_both_rows_to_the_same_four() -> None:
    layout = with_buttons(SOUTHPAW, sets.NEO_GEO)
    assert layout.attacks["a"] is layout.attacks["z"]
    assert set(layout.attacks.values()) == set(sets.NEO_GEO.buttons)


def test_bound_rows_keep_the_panel_shape() -> None:
    """The display draws these, so a short row has to stay a short row."""
    layout = with_buttons(SOUTHPAW, sets.MORTAL_KOMBAT)
    assert [[button.value for _, button in row] for row in layout.bound_rows()] == [["HP", "BL", "HK"], ["LP", "LK"]]


def test_the_slant_only_moves_the_neo_geo() -> None:
    assert sets.arrangement(sets.NEO_GEO, slanted_neo_geo=True) is sets.NEO_GEO_SLANT
    assert sets.arrangement(sets.NEO_GEO, slanted_neo_geo=False) is sets.NEO_GEO
    for other in (sets.STREET_FIGHTER, sets.TEKKEN, sets.MORTAL_KOMBAT, sets.EIGHT_BUTTON):
        assert sets.arrangement(other, slanted_neo_geo=True) is other


def test_every_offered_set_fits_every_layout() -> None:
    """A set with more buttons than a layout has keys would strand one."""
    for layout in (HITBOX, SOUTHPAW, GAMEPAD):
        for button_set in sets.BUTTON_SETS:
            bound = with_buttons(layout, button_set)
            assert set(bound.attacks.values()) == set(button_set.buttons), f"{layout.key} / {button_set.key}"


def test_an_unknown_set_falls_back_rather_than_failing() -> None:
    assert sets.get_set("moon-buggy") is sets.STREET_FIGHTER
