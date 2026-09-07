"""3rd Strike, Ken. Two fireballs in a row must not become a super.

Shouryuu Reppa is qcf, qcf+P, so a lenient trainer hands it to anyone who
throws two fireballs. The game clears the command buffer when a special comes
out, and so does the trainer unless the loose buffer rule is on.
"""

from __future__ import annotations

from tests.engine.test_motions.harness import DOWN, FORWARD, HP, Script, press, release

# The second fireball starts well clear of the first. Started sooner, the
# forward left over from the first plus the down of the second make a genuine
# forward, down, down-forward, and 3rd Strike gives a shouryuuken for it.
TWO_FIREBALLS: Script = [
    press(DOWN, 0),
    press(FORWARD, 70),
    release(DOWN, 110),
    press(HP, 150),
    release(HP, 190),
    release(FORWARD, 220),
    press(DOWN, 700),
    press(FORWARD, 770),
    release(DOWN, 810),
    press(HP, 850),
]


def test_two_fireballs_stay_two_fireballs(play) -> None:
    assert play(TWO_FIREBALLS).moves == ["Hadou Ken", "Hadou Ken"]


def test_the_second_fireball_does_not_become_a_super(play) -> None:
    assert "Shouryuu Reppa" not in play(TWO_FIREBALLS).moves
