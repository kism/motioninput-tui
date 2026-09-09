"""Ultra SF4, Sakura. Her two qcb,qcb supers differ only by button count, so
the three-kick one must not be eaten by the one-kick one landing first.
"""

from tests.engine.test_motions.harness import BACK, DOWN, HK, LK, MK, Script, press, release


def _double_qcb(*buttons: str) -> Script:
    """qcb, qcb, then the given kicks pressed together at the end."""
    return [
        press(DOWN, 0),
        press(BACK, 60),
        release(DOWN, 100),
        release(BACK, 150),
        press(DOWN, 200),
        press(BACK, 260),
        release(DOWN, 300),
        *(press(button, 340 + i * 8) for i, button in enumerate(buttons)),
        *(release(button, 400 + i * 8) for i, button in enumerate(buttons)),
    ]


def test_three_kicks_is_the_kkk_super(play) -> None:
    """qcb,qcb + KKK is Haru Ranman, not Haru Ichiban (qcb,qcb + K)."""
    assert play(_double_qcb(HK, MK, LK)).moves == ["Haru Ranman"]


def test_one_kick_is_the_k_super(play) -> None:
    """A single kick on the same motion still gives Haru Ichiban, once the
    grace window for the other two has passed."""
    assert play(_double_qcb(LK)).moves == ["Haru Ichiban"]
