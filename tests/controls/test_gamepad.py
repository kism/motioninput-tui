"""Turning a pad's state into binding codes, and the reader that polls it."""

from __future__ import annotations

import pytest

from motioninput_tui.controls import gamepad
from motioninput_tui.controls.gamepad import GamepadReader, codes_from_joystick, diff_codes
from motioninput_tui.controls.layouts import GAMEPAD
from motioninput_tui.engine.session import TrainingSession
from motioninput_tui.games.loader import load_game


class FakeJoystick:
    """A pad frozen in one state, enough of pygame's Joystick for the reader."""

    def __init__(
        self,
        *,
        buttons: tuple[bool, ...] = (),
        axes: tuple[float, ...] = (0.0, 0.0),
        hat: tuple[int, int] = (0, 0),
    ) -> None:
        self._buttons = buttons
        self._axes = axes
        self._hat = hat

    def init(self) -> None: ...
    def get_name(self) -> str:
        return "Fake Pad"

    def get_numbuttons(self) -> int:
        return len(self._buttons)

    def get_button(self, index: int) -> bool:
        return self._buttons[index]

    def get_numaxes(self) -> int:
        return len(self._axes)

    def get_axis(self, index: int) -> float:
        return self._axes[index]

    def get_numhats(self) -> int:
        return 1

    def get_hat(self, index: int) -> tuple[int, int]:
        return self._hat


def test_a_centred_pad_holds_nothing() -> None:
    assert codes_from_joystick(FakeJoystick()) == frozenset()


def test_the_left_stick_reads_as_a_direction() -> None:
    assert codes_from_joystick(FakeJoystick(axes=(-1.0, 0.0))) == {"pad:left"}
    assert codes_from_joystick(FakeJoystick(axes=(0.0, 1.0))) == {"pad:down"}


def test_a_stick_inside_the_deadzone_is_still_neutral() -> None:
    assert codes_from_joystick(FakeJoystick(axes=(0.3, -0.3))) == frozenset()


def test_the_dpad_reads_as_a_direction() -> None:
    assert codes_from_joystick(FakeJoystick(hat=(0, 1))) == {"pad:up"}
    assert codes_from_joystick(FakeJoystick(hat=(-1, 0))) == {"pad:left"}


def test_stick_and_dpad_diagonals_combine() -> None:
    assert codes_from_joystick(FakeJoystick(axes=(0.0, 1.0), hat=(-1, 0))) == {"pad:down", "pad:left"}


def test_only_the_first_six_buttons_are_bound() -> None:
    held = (False, False, True, False, False, False, True, True)
    assert codes_from_joystick(FakeJoystick(buttons=held)) == {"pad:2"}


def test_diff_reports_releases_before_presses() -> None:
    assert diff_codes(frozenset({"pad:left"}), frozenset({"pad:right"})) == [("pad:left", False), ("pad:right", True)]
    assert diff_codes(frozenset(), frozenset({"pad:0"})) == [("pad:0", True)]
    assert diff_codes(frozenset({"pad:0"}), frozenset({"pad:0"})) == []


def test_reader_without_pygame_reports_no_events(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gamepad, "_load_pygame", lambda: None)
    reader = GamepadReader()
    assert not reader.available
    assert not reader.connected
    assert reader.poll(0) == []


class FakePygame:
    """Just the pygame surface the reader touches."""

    error = RuntimeError

    def __init__(self, joystick: FakeJoystick | None) -> None:
        self._joystick = joystick
        self.event = self  # pump() lives here
        self.joystick = self

    def pump(self) -> None: ...
    def get_count(self) -> int:
        return 1 if self._joystick is not None else 0

    def Joystick(self, index: int) -> FakeJoystick:  # ruff: ignore[invalid-function-name] - mirrors pygame's class name
        assert self._joystick is not None
        return self._joystick


def test_reader_opens_a_pad_and_diffs_its_state(monkeypatch: pytest.MonkeyPatch) -> None:
    pad = FakeJoystick()
    monkeypatch.setattr(gamepad, "_load_pygame", lambda: FakePygame(pad))
    reader = GamepadReader()

    assert reader.poll(0) == []
    assert reader.connected

    pad._buttons = (False, False, True)
    assert reader.poll(10) == [("pad:2", True)]
    pad._buttons = (False, False, False)
    assert reader.poll(20) == [("pad:2", False)]


def test_gamepad_layout_makes_the_session_exact_even_without_a_terminal() -> None:
    game = load_game("sfiii3")
    session = TrainingSession(game, game.character("ryu"), GAMEPAD)
    assert session.gamepad is not None
    assert session.exact_input
    assert session.gamepad_waiting  # no pad plugged in during tests
    assert session.tick(0) is False


class ScriptedGamepad:
    """A gamepad reader that replays a fixed list of events, one poll at a time."""

    def __init__(self, polls: list[list[tuple[str, bool]]]) -> None:
        self._polls = polls
        self.connected = True

    def poll(self, at_ms: int) -> list[tuple[str, bool]]:
        return self._polls.pop(0) if self._polls else []

    def reset(self) -> None: ...


def test_a_quarter_circle_on_the_pad_is_a_fireball() -> None:
    game = load_game("sfiii3")
    session = TrainingSession(game, game.character("ryu"), GAMEPAD)
    session.gamepad = ScriptedGamepad(  # ty: ignore[invalid-assignment]
        [
            [("pad:down", True)],  # d
            [("pad:right", True)],  # df, still holding down
            [("pad:down", False)],  # f
            [("pad:2", True)],  # LP
        ]
    )
    for at_ms in (0, 60, 110, 150):
        session.tick(at_ms)

    assert [entry.direction.short for entry in session.entries if entry.direction.short != "n"] == ["d", "df", "f"]
    assert [activation.name for activation in session.activations] == ["Hadou Ken"]
