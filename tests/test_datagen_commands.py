"""Correcting a guide that has a move's command wrong.

The mechanism matters more than the one entry using it: an override that
silently stops applying - a guide edited, a move renamed - would put the wrong
input back in front of the player with nothing to say it had happened.
"""

import pytest

from motioninput_tui.controls.buttons import NEO_GEO, STREET_FIGHTER
from motioninput_tui.engine.motions import MotionKind
from motioninput_tui.games.loader import load_game
from motioninput_tui.games.models import Category, Character, Move
from motioninput_tui_datagen.commands import OVERRIDES, apply_command_overrides
from motioninput_tui_datagen.normalise import parse_command


def _character(*moves: Move) -> Character:
    return Character(key="sakura", name="Sakura", title="", moves=moves)


def _move(name: str, command: str) -> Move:
    parsed = parse_command(command)
    return Move(name=name, command=command, category=Category.SUPER, motion=parsed.motion)


def test_every_override_names_a_move_that_exists() -> None:
    """The guarantee the whole table rests on. A correction that matches nothing
    is worse than no correction, since the roster keeps the guide's version."""
    for game_key, table in OVERRIDES.items():
        roster = {
            (character.key, move.name) for character in load_game(game_key).characters for move in character.moves
        }
        missing = sorted(entry for entry in table if entry not in roster)
        assert not missing, f"{game_key}: no such move {missing}"


def test_every_override_parses() -> None:
    """A correction the parser cannot read would leave the guide's command in
    place, which is the one outcome that looks like nothing happened."""
    for game_key, table in OVERRIDES.items():
        for entry, command in table.items():
            assert parse_command(command).motion is not None, f"{game_key} {entry}: {command!r} does not parse"


def test_sakuras_super_is_corrected_in_the_roster() -> None:
    """The entry itself, checked on the generated data rather than the table."""
    move = next(m for m in load_game("sfa3").character("sakura").moves if m.name == "Midare-zakura")
    assert move.command == "qcf,qcf + K"
    assert move.motion is not None
    assert move.motion.kind is MotionKind.QCF_X2


def test_a_correction_replaces_the_command_and_the_motion() -> None:
    corrected = apply_command_overrides("sfa3", [_character(_move("Midare-zakura", "qcf,d,df + K"))], STREET_FIGHTER)
    move = corrected[0].moves[0]
    assert move.command == "qcf,qcf + K"
    assert move.motion is not None
    assert move.motion.kind is MotionKind.QCF_X2


def test_moves_without_a_correction_are_left_alone() -> None:
    untouched = _move("Shinkuu Hadou Ken", "qcf,qcf + P")
    corrected = apply_command_overrides("sfa3", [_character(untouched)], STREET_FIGHTER)
    assert corrected[0].moves[0] == untouched


def test_a_game_with_no_table_is_returned_unchanged() -> None:
    character = _character(_move("Hadou Ken", "qcf + P"))
    assert apply_command_overrides("sfiii3", [character], STREET_FIGHTER) == [character]


def test_a_correction_that_matches_nothing_warns(caplog: pytest.LogCaptureFixture) -> None:
    apply_command_overrides("sfa3", [_character(_move("Some Other Move", "qcf + P"))], STREET_FIGHTER)
    assert "No move" in caplog.text
    assert "Midare-zakura" in caplog.text


def test_a_neo_geo_roster_keeps_its_own_panel(monkeypatch: pytest.MonkeyPatch) -> None:
    """The engine matches buttons by identity, so a correction on a Neo Geo game
    has to come back as A B C D and not the Street Fighter six it was parsed as."""
    monkeypatch.setitem(OVERRIDES, "lastbld2", {("yuki", "HyouJin"): "qcf + K"})
    corrected = apply_command_overrides(
        "lastbld2", [Character(key="yuki", name="Yuki", title="", moves=(_move("HyouJin", "d, df, f + A"),))], NEO_GEO
    )
    motion = corrected[0].moves[0].motion
    assert motion is not None
    assert {button.value for button in motion.buttons.allowed} == {"B", "D"}
