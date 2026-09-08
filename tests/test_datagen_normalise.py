"""Command normalisation, focused on the mash-vs-motion distinction.

A command whose only cue is "tap P rapidly" is a mash. A real motion that ends
in "tap P rapidly" for extra hits (most 3rd Strike and KoF supers) is that
motion, not a mash - the tail is decoration.
"""

import pytest

from motioninput_tui.engine.motions import MotionKind
from motioninput_tui_datagen.normalise import parse_command


@pytest.mark.parametrize(
    ("command", "kind"),
    [
        ("Tap P rapidly", MotionKind.MASH),
        ("press any Punch rapidly", MotionKind.MASH),
        ("qcf,qcf + P, tap P rapidly   x2", MotionKind.QCF_X2),  # Sean's Shouryuu Cannon
        ("qcf,qcf + P   x2", MotionKind.QCF_X2),
        ("f,d,df + P, tap P rapidly", MotionKind.DP),  # Necro's Denji Blast
        ("qcb,d,db + K, tap P / K rapidly", MotionKind.QCB_RDP),
        ("Charge Down for 2 secs, Up + any Punch, press P rapidly", MotionKind.CHARGE_DU),  # Dee Jay's Hyper Fist
    ],
)
def test_a_mashable_tail_does_not_hide_the_motion(command: str, kind: MotionKind) -> None:
    motion = parse_command(command).motion
    assert motion is not None
    assert motion.kind is kind


def test_an_air_super_with_a_mashable_tail_stays_airborne() -> None:
    motion = parse_command("In air, qcf,qcf + P, tap P rapidly    x3").motion
    assert motion is not None
    assert motion.kind is MotionKind.QCF_X2
    assert motion.air
