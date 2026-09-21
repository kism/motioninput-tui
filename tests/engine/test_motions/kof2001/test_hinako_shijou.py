"""KoF 2001, Hinako Shijou. A comma between buttons is a string, not a choice."""

from tests.engine.test_motions.harness import FORWARD, NEO_A, NEO_C, press, release


def test_forward_a_then_c_is_harite_nishiki(play) -> None:
    script = [press(FORWARD, 0), press(NEO_A, 50), release(NEO_A, 90), press(NEO_C, 250)]
    assert play(script).moves[-1] == "Harite Nishiki"


def test_forward_c_alone_is_not(play) -> None:
    assert "Harite Nishiki" not in play([press(FORWARD, 0), press(NEO_C, 50)]).moves
