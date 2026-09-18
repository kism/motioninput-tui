"""Command normalisation, focused on the mash-vs-motion distinction.

A command whose only cue is "tap P rapidly" is a mash. A real motion that ends
in "tap P rapidly" for extra hits (most 3rd Strike and KoF supers) is that
motion, not a mash - the tail is decoration.
"""

import pytest

from motioninput_tui.engine.motions import MotionKind
from motioninput_tui_datagen.neogeo import to_neo_panel, to_shorthand
from motioninput_tui_datagen.normalise import _MASH_DEFAULT, parse_command


@pytest.mark.parametrize(
    ("command", "kind", "mash"),
    [
        ("Tap P rapidly", MotionKind.MASH, 0),
        ("press any Punch rapidly", MotionKind.MASH, 0),
        ("qcf,qcf + P, tap P rapidly   x2", MotionKind.QCF_X2, _MASH_DEFAULT),  # Sean's Shouryuu Cannon
        ("qcf,qcf + P   x2", MotionKind.QCF_X2, 0),
        ("f,d,df + P, tap P rapidly", MotionKind.DP, _MASH_DEFAULT),  # Necro's Denji Blast
        ("qcb,d,db + K, tap P / K rapidly", MotionKind.QCB_RDP, _MASH_DEFAULT),
        ("Charge Down for 2 secs, Up + any Punch, press P rapidly", MotionKind.CHARGE_DU, _MASH_DEFAULT),  # Dee Jay
    ],
)
def test_a_mashable_tail_does_not_hide_the_motion(command: str, kind: MotionKind, mash: int) -> None:
    motion = parse_command(command).motion
    assert motion is not None
    assert motion.kind is kind
    assert motion.mash == mash


def test_an_air_super_with_a_mashable_tail_stays_airborne() -> None:
    motion = parse_command("In air, qcf,qcf + P, tap P rapidly    x3").motion
    assert motion is not None
    assert motion.kind is MotionKind.QCF_X2
    assert motion.air
    assert motion.mash == _MASH_DEFAULT


def test_a_deliberate_tap_tail_is_a_rhythm_follow_through() -> None:
    """Sakura Otoshi: dp + K, then three deliberate P taps (not a mash)."""
    motion = parse_command("f,d,df + K, tap P,P,P").motion
    assert motion is not None
    assert motion.kind is MotionKind.DP
    assert motion.buttons.label == "K"
    assert motion.mash == _MASH_DEFAULT  # three taps
    assert motion.mash_rhythm is True
    assert motion.mash_button == "P"  # the taps are the other button


def test_a_rapid_tail_is_not_a_rhythm_one() -> None:
    motion = parse_command("qcf,qcf + P, tap P rapidly").motion
    assert motion is not None
    assert motion.mash == _MASH_DEFAULT
    assert motion.mash_rhythm is False
    assert not motion.mash_button


@pytest.mark.parametrize(
    "command",
    [
        "qcb + K  (air)",  # Ryu / Ken / Sakura hurricane kick: ground or air
        "f,d,df + P  (air)",
        "qcf + P (can also be done in air)",
    ],
)
def test_the_air_marker_is_not_an_airborne_requirement(command: str) -> None:
    """Every guide's legend: trailing '(air)' means ground *or* air, so a plain
    ground input must satisfy it. Only an 'In air,' prefix is a real requirement."""
    motion = parse_command(command).motion
    assert motion is not None
    assert not motion.air


def test_a_bare_mash_keeps_the_ruleset_count_not_the_tail_default() -> None:
    """A standalone mash is MotionKind.MASH and carries no per-move count."""
    motion = parse_command("Tap P rapidly").motion
    assert motion is not None
    assert motion.mash == 0


@pytest.mark.parametrize(
    ("command", "kind"),
    [
        # KoF '98 writes these as shorthand, KoF 2001 as numpad. Both mean one
        # roll of the stick, sharing the direction the two halves meet on.
        ("qcf,hcb + P", MotionKind.QCF_HCB),
        ("d,df,f,df,d,db,b + P", MotionKind.QCF_HCB),
        ("qcb,hcf + P", MotionKind.QCB_HCF),
        ("d,db,b,db,d,df,f + P", MotionKind.QCB_HCF),
        ("hcb,f + P", MotionKind.HCB_F),
        ("f,df,d,db,b,f + P", MotionKind.HCB_F),
        # The two SNK rolls. `qcb,db,f` turns back on itself and `f,hcf`
        # taps forward first, so neither reduces to the plain motion inside
        # it the way a run of shorthands does.
        ("d,db,b,db,f + P", MotionKind.QCB_DB_F),
        ("qcb,db,f + P", MotionKind.QCB_DB_F),
        ("f,b,db,d,df,f + P", MotionKind.F_HCF),
        ("f,hcf + P", MotionKind.F_HCF),
        # Shorthands that meet on different directions are untouched by the
        # sharing, and a repeat the guide wrote itself is still two presses.
        ("qcf,qcf + P", MotionKind.QCF_X2),
        ("hcb,hcb + P", MotionKind.HCB_X2),
    ],
)
def test_a_run_of_shorthands_shares_the_direction_they_meet_on(command: str, kind: MotionKind) -> None:
    motion = parse_command(command).motion
    assert motion is not None
    assert motion.kind is kind


@pytest.mark.parametrize(
    ("command", "kind"),
    [
        ("F, DF, D + any Punch", MotionKind.F_DF_D),  # Zangief's Banishing Flat
        ("b,db,d + K", MotionKind.B_DB_D),  # Sodom's Tengu Walking
        ("Charge db,f + K", MotionKind.CHARGE_DB_F),  # Vega's Scarlet Terror
        ("Charge b,f + K", MotionKind.CHARGE_BF),
        ("P repeatedly", MotionKind.MASH),  # Clark's Vulcan Punch
    ],
)
def test_shapes_the_guides_share(command: str, kind: MotionKind) -> None:
    motion = parse_command(command).motion
    assert motion is not None
    assert motion.kind is kind


@pytest.mark.parametrize(
    "command",
    [
        # Jupiter's Giant Swing, walked round the gate rather than written "360".
        "F DF D DB B UB U UF + any Punch",
        # And the same circle taken the other way about.
        "F UF U UB B DB D DF + any Punch",
    ],
)
def test_a_circle_spelled_out_is_still_a_rotation(command: str) -> None:
    """Not every guide writes a 360 as "360"; one that names all eight
    directions in order means the same input."""
    motion = parse_command(command).motion
    assert motion is not None
    assert motion.kind is MotionKind.ROTATE_360


@pytest.mark.parametrize(
    "command",
    [
        # Uranus' Destructive Carnival: out to back and home again, which covers
        # most of the ring twice over without ever going right round it.
        "F DF D DB B DB D DF F + Strong Kick",
        # And her Diving Gaia Crash, which stops one notch short of the turn.
        "F DF D DB B UB U + Strong Kick",
    ],
)
def test_a_long_motion_that_never_goes_right_round_is_not_a_rotation(command: str) -> None:
    """The guard on the rule above: plenty of directions is not a circle, or
    every rambling command throw in the rosters would become a 360."""
    motion = parse_command(command).motion
    assert motion is None or motion.kind is not MotionKind.ROTATE_360


def test_a_neo_geo_mash_keeps_its_button() -> None:
    """Kuroko's ``C rapidly`` has no ``+`` for the button translation to find."""
    command = "C rapidly"
    motion = parse_command(to_shorthand(command)).motion
    assert motion is not None
    assert motion.kind is MotionKind.MASH
    assert to_neo_panel(motion, command).buttons.label == "C"
