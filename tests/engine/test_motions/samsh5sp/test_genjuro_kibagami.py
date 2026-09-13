"""SSV Special, Genjuro. The Rage supers, which want two buttons at once.

Every character's two supers are `qcf + CD` and `qcb + CD`, the game's own
marker for needing a full Rage gauge. The trainer models the input, not the
meter, so they come out whenever the motion and both buttons do.

Genjuro is the clean case: nothing else of his answers a quarter circle with C
alone. Where a character does have a single-button move on the same motion, the
recogniser holds the press for `BUTTON_GRACE_MS` to see whether the rest of the
pair arrives -- see `test_haohmaru.py`, whose `qcf + C` fireball no longer eats
the `qcf + CD` Rage super.
"""

from tests.engine.test_motions.harness import DOWN, FORWARD, NEO_A, NEO_C, NEO_D, Script, press, release


def _quarter_circle(*buttons: str) -> Script:
    return [
        press(DOWN, 0),
        press(FORWARD, 70),
        release(DOWN, 110),
        *(press(button, 150) for button in buttons),
    ]


def test_quarter_circle_with_both_super_buttons_is_the_rage_super(play) -> None:
    assert play(_quarter_circle(NEO_C, NEO_D)).moves == ["Gokou Zan"]


def test_a_slash_on_the_same_motion_is_the_ordinary_special(play) -> None:
    assert play(_quarter_circle(NEO_A)).moves == ["Sanren Satsu: Kiba"]


def test_one_of_the_two_super_buttons_alone_is_not_enough(play) -> None:
    assert play(_quarter_circle(NEO_C)).moves == []
