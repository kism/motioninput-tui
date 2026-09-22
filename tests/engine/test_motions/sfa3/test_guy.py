"""Alpha 3, Guy. Two Bushin strings that are the same four presses.

`LP,MP,HP,HK` is the Gokusa Ken and `LP,MP,HP, d + HK` the Seoi Nage. Nothing
separates them but the down held for the last press, so this is where a
sequence's final direction is checked - and where the recogniser has to prefer
the move that asks for it.
"""

from tests.engine.test_motions.harness import DOWN, HK, HP, LP, MP, Script, press, release

RUN: Script = [
    press(LP, 0),
    release(LP, 40),
    press(MP, 180),
    release(MP, 220),
    press(HP, 360),
    release(HP, 400),
]


def test_the_plain_run_is_the_gokusa_ken(play) -> None:
    assert play([*RUN, press(HK, 540)]).moves == ["Bushin Gokusa Ken"]


def test_holding_down_for_the_last_press_is_the_seoi_nage(play) -> None:
    assert play([*RUN, press(DOWN, 500), press(HK, 540)]).moves == ["Bushin-ryuu Seoi Nage"]


def test_the_run_without_its_last_press_is_nothing(play) -> None:
    assert play(RUN).moves == []
