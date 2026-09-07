"""The gamepad probe's pure helpers (the SDL parts need real hardware)."""

from __future__ import annotations

import re

from motioninput_tui import gamepad_probe
from motioninput_tui.controls import gamepad
from motioninput_tui.gamepad_probe import _report_path, _slug, _snapshot


class FakeJoystick:
    def __init__(self, buttons: tuple[bool, ...] = (), axes: tuple[float, ...] = (), hats: tuple = ()) -> None:
        self._b, self._a, self._h = buttons, axes, hats

    def get_name(self) -> str:
        return "Fake"

    def get_guid(self) -> str:
        return "0" * 32

    def get_numbuttons(self) -> int:
        return len(self._b)

    def get_button(self, index: int) -> bool:
        return self._b[index]

    def get_numaxes(self) -> int:
        return len(self._a)

    def get_axis(self, index: int) -> float:
        return self._a[index]

    def get_numhats(self) -> int:
        return len(self._h)

    def get_hat(self, index: int):
        return self._h[index]


class FakePad:
    name = "Fake"

    def __init__(self, buttons: set[int] | None = None, axes: dict[int, float] | None = None) -> None:
        self._b, self._a = buttons or set(), axes or {}

    def get_button(self, button: int) -> int:
        return int(button in self._b)

    def get_axis(self, axis: int) -> float:
        return self._a.get(axis, 0.0)


def test_slug_is_filename_safe() -> None:
    assert _slug("PS3 Controller") == "PS3-Controller"
    assert _slug("8BitDo Pro 2 (v3.02)") == "8BitDo-Pro-2-v3-02"
    assert _slug("???") == "pad"


def test_report_path_carries_pad_name_and_a_timestamp() -> None:
    path = _report_path("PS3 Controller")
    assert path.parent == gamepad_probe._REPORT_DIR
    assert "PS3-Controller" in path.name
    assert re.search(r"_\d{8}-\d{6}\.txt$", path.name)


def test_snapshot_shows_what_the_trainer_would_see() -> None:
    joystick = FakeJoystick(buttons=(False,) * 15, axes=(0.0,) * 6, hats=())
    pad = FakePad(buttons={gamepad._BUTTON_DPAD_LEFT}, axes={gamepad._AXIS_LEFTY: gamepad.AXIS_MAX})
    line = _snapshot(joystick, pad, {gamepad._BUTTON_DPAD_LEFT: "DPAD_LEFT"}, {gamepad._AXIS_LEFTY: "LEFTY"})
    assert "DPAD_LEFT" in line
    assert "LEFTY=+1.00" in line  # raw int16 scaled back to -1.0..1.0
    assert "trainer sees: ['pad:down', 'pad:left']" in line


def test_snapshot_without_a_controller_is_just_the_raw_view() -> None:
    line = _snapshot(FakeJoystick(buttons=(True,), axes=(), hats=()), None, {}, {})
    assert line == "raw: buttons=[0] axes=[] hats=[]"
