"""Turning a pad's state into binding codes, and the reader that polls it."""

import pytest

from motioninput_tui.controls import gamepad
from motioninput_tui.controls.buttons import NEO_GEO
from motioninput_tui.controls.gamepad import GamepadReader, codes_from_pad, diff_codes
from motioninput_tui.controls.layouts import GAMEPAD, gamepad_layout, resolve_gamepad_bindings, with_buttons
from motioninput_tui.engine.notation import Button
from motioninput_tui.engine.session import TrainingSession
from motioninput_tui.games.loader import load_game

_FULL = gamepad.AXIS_MAX  # SDL reports a fully deflected axis as this raw value


class FakePad:
    """A game controller frozen in one state, read via SDL's semantic API.

    ``axes`` values are the raw signed-16-bit range SDL's controller API uses,
    not -1.0..1.0.
    """

    name = "Fake Pad"

    def __init__(self, *, buttons: tuple[int, ...] = (), axes: dict[int, float] | None = None) -> None:
        self._buttons = set(buttons)
        self._axes = axes or {}

    def get_button(self, button: int) -> int:
        return int(button in self._buttons)

    def get_axis(self, axis: int) -> float:
        return self._axes.get(axis, 0.0)


def test_a_centred_pad_holds_nothing() -> None:
    assert codes_from_pad(FakePad()) == frozenset()


def test_the_left_stick_reads_as_a_direction() -> None:
    assert codes_from_pad(FakePad(axes={gamepad._AXIS_LEFTX: -_FULL})) == {"pad:left"}
    assert codes_from_pad(FakePad(axes={gamepad._AXIS_LEFTY: _FULL})) == {"pad:down"}


def test_a_stick_inside_the_deadzone_is_still_neutral() -> None:
    small = round(0.3 * _FULL)
    assert codes_from_pad(FakePad(axes={gamepad._AXIS_LEFTX: small, gamepad._AXIS_LEFTY: -small})) == frozenset()


def test_a_stick_resting_a_few_counts_off_zero_is_not_a_direction() -> None:
    # A DualShock 3 / GP2040 in PS3 mode sits at about -129 raw on every axis;
    # without scaling by AXIS_MAX that read as holding left and up forever.
    resting = dict.fromkeys((gamepad._AXIS_LEFTX, gamepad._AXIS_LEFTY), -129.0)
    assert codes_from_pad(FakePad(axes=resting)) == frozenset()


def test_the_dpad_reads_as_a_direction() -> None:
    assert codes_from_pad(FakePad(buttons=(gamepad._BUTTON_DPAD_UP,))) == {"pad:up"}
    assert codes_from_pad(FakePad(buttons=(gamepad._BUTTON_DPAD_LEFT,))) == {"pad:left"}


def test_stick_and_dpad_diagonals_combine() -> None:
    pad = FakePad(buttons=(gamepad._BUTTON_DPAD_LEFT,), axes={gamepad._AXIS_LEFTY: _FULL})
    assert codes_from_pad(pad) == {"pad:down", "pad:left"}


def test_face_and_shoulder_buttons_map_to_their_codes() -> None:
    assert codes_from_pad(FakePad(buttons=(gamepad._BUTTON_X,))) == {"pad:2"}
    assert codes_from_pad(FakePad(buttons=(gamepad._BUTTON_RIGHTSHOULDER,))) == {"pad:5"}


def test_a_pulled_trigger_counts_as_a_button() -> None:
    assert codes_from_pad(FakePad(axes={gamepad._AXIS_TRIGGERRIGHT: _FULL})) == {"pad:7"}
    assert codes_from_pad(FakePad(axes={gamepad._AXIS_TRIGGERLEFT: round(0.1 * _FULL)})) == frozenset()


def test_diff_reports_releases_before_presses() -> None:
    assert diff_codes(frozenset({"pad:left"}), frozenset({"pad:right"})) == [("pad:left", False), ("pad:right", True)]
    assert diff_codes(frozenset(), frozenset({"pad:0"})) == [("pad:0", True)]
    assert diff_codes(frozenset({"pad:0"}), frozenset({"pad:0"})) == []


def test_reader_without_pygame_reports_no_events(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gamepad, "load_pygame", lambda: None)
    reader = GamepadReader()
    assert not reader.available
    assert not reader.connected
    assert reader.poll(0) == []
    assert reader.name is None


def test_reader_reports_the_open_pad_name(monkeypatch: pytest.MonkeyPatch) -> None:
    pad = FakePad()
    monkeypatch.setattr(gamepad, "load_pygame", FakePygame)
    monkeypatch.setattr(gamepad, "_first_controller", lambda _pygame: pad)
    reader = GamepadReader()
    assert reader.name is None  # nothing opened yet
    reader.poll(0)
    assert reader.name == "Fake Pad"


def test_default_gamepad_layout_is_the_shared_instance() -> None:
    default_lp = next(code for code, button in GAMEPAD.attacks.items() if button is Button.LP)
    assert gamepad_layout() is GAMEPAD
    assert gamepad_layout({}) is GAMEPAD
    assert gamepad_layout({"LP": default_lp}) is GAMEPAD  # a no-op rebind


def test_gamepad_layout_applies_a_rebind() -> None:
    # HP and MK trade pad buttons, as the bind screen's swap would produce.
    layout = gamepad_layout({"HP": "pad:1", "MK": "pad:5"})
    assert layout is not GAMEPAD
    assert layout.attacks["pad:1"] is Button.HP
    assert layout.attacks["pad:5"] is Button.MK
    assert len(layout.attacks) == len(GAMEPAD.attacks)  # nothing stranded
    assert layout.movement == GAMEPAD.movement  # movement untouched


def test_a_rebind_keeps_the_panel_in_its_street_fighter_grid() -> None:
    """The input display draws `bound_rows`; a trigger rebind must not ragged it.

    HK on the right trigger (`pad:7`, which `GAMEPAD_ROWS` lists in the top row)
    used to jump up beside HP, leaving `LK MK` stranded below.
    """
    layout = gamepad_layout({"HK": "pad:7"})
    assert [[button.value for _, button in row] for row in layout.bound_rows()] == [
        ["LP", "MP", "HP"],
        ["LK", "MK", "HK"],
    ]


def test_a_rebind_still_lays_a_wider_set_on() -> None:
    """A spare code trails each row so the Neo Geo's fourth button still binds."""
    layout = with_buttons(gamepad_layout({"HK": "pad:7"}), NEO_GEO)
    assert [len(row) for row in layout.bound_rows()] == [4, 4]


def test_gamepad_layout_ignores_junk_and_collisions() -> None:
    assert gamepad_layout({"NOPE": "pad:0", "LP": "keyboard"}) is GAMEPAD
    # Two attacks pointed at one pad button would strand a third: fall back whole.
    collision = {"LP": "pad:0", "LK": "pad:0"}
    assert resolve_gamepad_bindings(collision) == resolve_gamepad_bindings(None)


class FakePygame:
    """Just the pygame surface the reader touches: ``event.pump()`` and ``error``."""

    error = RuntimeError

    def __init__(self) -> None:
        self.event = self  # pump() lives here

    def pump(self) -> None: ...


def test_reader_opens_a_pad_and_diffs_its_state(monkeypatch: pytest.MonkeyPatch) -> None:
    pad = FakePad()
    monkeypatch.setattr(gamepad, "load_pygame", FakePygame)
    monkeypatch.setattr(gamepad, "_first_controller", lambda _pygame: pad)
    reader = GamepadReader()

    assert reader.poll(0) == []
    assert reader.connected

    pad._buttons = {gamepad._BUTTON_X}
    assert reader.poll(10) == [("pad:2", True)]
    assert reader.held_codes == {"pad:2"}  # what the input display lights the panel from
    pad._buttons = set()
    assert reader.poll(20) == [("pad:2", False)]
    assert reader.held_codes == frozenset()


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
