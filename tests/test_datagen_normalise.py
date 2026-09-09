"""Command normalisation, focused on the mash-vs-motion distinction.

A command whose only cue is "tap P rapidly" is a mash. A real motion that ends
in "tap P rapidly" for extra hits (most 3rd Strike and KoF supers) is that
motion, not a mash - the tail is decoration.
"""

import pytest

from motioninput_tui.engine.motions import MotionKind
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
