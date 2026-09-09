"""Ultra SF4, Balrog. Charge b,f and its double; charge b,df is not modelled."""

from tests.engine.test_motions.harness import BACK, DOWN, FORWARD, HP, LP, UP, press, release


def test_charge_back_forward_is_a_dash_straight(play) -> None:
    script = [
        press(BACK, 0),
        release(BACK, 960),
        press(FORWARD, 970),
        press(HP, 990),
        release(HP, 1030),
    ]
    assert play(script).moves == ["Dash Straight"]


def test_charge_back_forward_back_forward_is_crazy_buffalo(play) -> None:
    script = [
        press(BACK, 0),
        release(BACK, 940),
        press(FORWARD, 950),
        release(FORWARD, 990),
        press(BACK, 1000),
        release(BACK, 1040),
        press(FORWARD, 1050),
        press(HP, 1070),
        release(HP, 1110),
    ]
    assert play(script).moves == ["Crazy Buffalo"]


def test_charge_down_up_is_a_buffalo_headbutt(play) -> None:
    script = [
        press(DOWN, 0),
        release(DOWN, 960),
        press(UP, 970),
        press(LP, 990),
        release(LP, 1030),
    ]
    assert play(script).moves == ["Buffalo Headbutt"]
