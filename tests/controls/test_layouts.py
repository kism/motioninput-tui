"""The keyboard layout list and the custom layout's rebinds."""

import pytest

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
)
from motioninput_tui.engine.notation import ALL_BUTTONS


def test_the_keyboard_choices_are_the_two_presets_and_the_custom_one() -> None:
    keyboard = [layout.key for layout in available_layouts() if layout.kind.value == "keyboard"]
    assert keyboard == ["keyboard-left", "keyboard-right", "keyboard-custom"]
    assert KB_LEFT.key == DEFAULT_LAYOUT


@pytest.mark.parametrize("layout", [KB_LEFT, KB_RIGHT], ids=lambda layout: layout.key)
def test_each_preset_carries_the_street_fighter_six(layout: ControlLayout) -> None:
    assert set(layout.attacks.values()) == ALL_BUTTONS


def test_the_default_custom_layout_is_the_shared_instance() -> None:
    assert keyboard_layout() is KB_CUSTOM
    assert keyboard_layout({}) is KB_CUSTOM
    assert keyboard_layout({"LP": "j"}) is KB_CUSTOM  # already the default


def test_a_rebind_moves_the_key_and_keeps_the_rest() -> None:
    layout = keyboard_layout({"LP": "semicolon", "up": "quotation_mark"})
    assert layout.attacks["semicolon"].value == "LP"
    assert "j" not in layout.attacks  # the old LP key is free
    assert layout.movement["quotation_mark"] is Axis.UP
    assert layout.movement["a"] is Axis.LEFT  # untouched
    assert ("semicolon", "k", "l") in layout.attack_rows  # rows rebuilt too


def test_a_collision_falls_back_to_the_whole_default() -> None:
    # LP onto the key MP already has: not a bijection.
    assert resolve_keyboard_bindings({"LP": "k"}) == KEYBOARD_DEFAULT_BINDINGS
    assert keyboard_layout({"LP": "k"}) is KB_CUSTOM


def test_junk_slots_and_empty_values_are_ignored() -> None:
    resolved = resolve_keyboard_bindings({"LP": "z", "nonsense": "q", "MP": ""})
    assert resolved["LP"] == "z"
    assert resolved["MP"] == KEYBOARD_DEFAULT_BINDINGS["MP"]
    assert "nonsense" not in resolved
