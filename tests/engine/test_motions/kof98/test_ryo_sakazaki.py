"""KoF '98, Ryo Sakazaki. The forward tap that turns a half circle into a super.

Ryo has both: `b,db,d,df,f + P` is the Kyokugen Renbuken and `f,b,db,d,df,f + P`
is the Haoh Shou Ko Ken, the same buttons on the same roll with one forward tap
in front of it. Nothing in Street Fighter is written this way, so the leading
forward has to be a step of the motion rather than leniency, or every Renbuken
done while walking forward would come out a super.
"""

from tests.engine.test_motions.harness import FORWARD_INTO_HALF_CIRCLE_FORWARD_HP

# The same roll without its opening tap, press and release, which is a plain half circle forward.
HALF_CIRCLE_FORWARD_HP = FORWARD_INTO_HALF_CIRCLE_FORWARD_HP[2:]


def test_a_forward_then_a_half_circle_is_the_haoh_shou_ko_ken(play) -> None:
    assert play(FORWARD_INTO_HALF_CIRCLE_FORWARD_HP).moves == ["Haoh Shou Ko Ken"]


def test_the_half_circle_alone_is_only_the_renbuken(play) -> None:
    assert play(HALF_CIRCLE_FORWARD_HP).moves == ["Kyokugen Renbuken"]
