"""The keyboard layout list and the custom layout's rebinds."""

import pytest

from motioninput_tui.controls.buttons import NEO_GEO
from motioninput_tui.controls.layouts import (
    DEFAULT_LAYOUT,
    KB_CUSTOM,
    KB_LEFT,
    KB_RIGHT,
    KEYBOARD_DEFAULT_BINDINGS,
    Axis,
    ControlLayout,
    available_layouts,
    keyboard_layout,
    resolve_keyboard_bindings,
    with_buttons,
)
from motioninput_tui.engine.notation import ALL_BUTTONS, Button


def test_the_keyboard_choices_are_the_two_presets_and_the_custom_one() -> None:
    keyboard = [layout.key for layout in available_layouts() if layout.kind.value == "keyboard"]
    assert keyboard == ["keyboard-left", "keyboard-right", "keyboard-custom"]
    assert KB_LEFT.key == DEFAULT_LAYOUT


@pytest.mark.parametrize("layout", [KB_LEFT, KB_RIGHT, KB_CUSTOM], ids=lambda layout: layout.key)
def test_each_keyboard_carries_the_street_fighter_six(layout: ControlLayout) -> None:
    assert set(layout.attacks.values()) == ALL_BUTTONS


@pytest.mark.parametrize("layout", [KB_LEFT, KB_RIGHT, KB_CUSTOM], ids=lambda layout: layout.key)
def test_each_keyboard_has_eight_attack_keys_so_the_neo_geo_reaches_d(layout: ControlLayout) -> None:
    assert [len(row) for row in layout.attack_rows] == [4, 4]
    assert set(with_buttons(layout, NEO_GEO).attacks.values()) == {Button.A, Button.B, Button.C, Button.D}


def test_the_default_custom_layout_is_the_shared_instance() -> None:
    assert keyboard_layout() is KB_CUSTOM
    assert keyboard_layout({}) is KB_CUSTOM
    assert keyboard_layout({"top1": "j"}) is KB_CUSTOM  # already the default


def test_a_rebind_moves_the_key_and_keeps_the_rest() -> None:
    layout = keyboard_layout({"top1": "u", "up": "quotation_mark"})
    assert layout.attacks["u"].value == "LP"
    assert "j" not in layout.attacks  # the old top1 key is free
    assert layout.movement["quotation_mark"] is Axis.UP
    assert layout.movement["a"] is Axis.LEFT  # untouched
    assert ("u", "k", "l", "semicolon") in layout.attack_rows  # rows rebuilt too


def test_a_slot_left_at_its_default_gives_way_to_a_key_the_player_chose() -> None:
    """A map saved before the fourth column existed may already use its keys."""
    resolved = resolve_keyboard_bindings({"top3": "semicolon"})
    assert resolved["top3"] == "semicolon"
    assert resolved["top4"] == "l"  # the key top3 let go of


def test_two_chosen_slots_on_one_key_fall_back_to_the_whole_default() -> None:
    assert resolve_keyboard_bindings({"top1": "k", "top2": "k"}) == KEYBOARD_DEFAULT_BINDINGS
    assert keyboard_layout({"top1": "k", "top2": "k"}) is KB_CUSTOM


def test_junk_slots_and_empty_values_are_ignored() -> None:
    resolved = resolve_keyboard_bindings({"top1": "z", "nonsense": "q", "top2": ""})
    assert resolved["top1"] == "z"
    assert resolved["top2"] == KEYBOARD_DEFAULT_BINDINGS["top2"]
    assert "nonsense" not in resolved
