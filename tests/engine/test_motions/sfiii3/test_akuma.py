"""3rd Strike, Akuma. The Hyakki Shuu dive, which this guide writes in ellipses.

Everything the dive leads to is listed under it as `...press P`, with no name
and no motion of its own: the `...` is the whole statement that the row
continues the one above. The dive itself ends `then...`, pointing down at them,
which is punctuation rather than an input - it is a plain `f,d,df + K`.

Worth a file because getting either of those wrong is invisible rather than
loud: the moves stay in the list, they just sit in the wrong section under a
motion the trainer never gives you.
"""

from tests.engine.test_motions.harness import DOWN, FORWARD, MK, Script, press, release

DIVE: Script = [
    press(FORWARD, 0),
    release(FORWARD, 50),
    press(DOWN, 90),
    press(FORWARD, 150),
    release(DOWN, 190),
    press(MK, 200),
]


def test_the_dive_is_a_dragon_punch_with_a_kick(play) -> None:
    """`f,d,df + K, then...` - the ellipsis points at the rows beneath it, so
    the input is the dragon punch on its own."""
    assert play(DIVE).moves == ["Hyakki Shuu"]


def test_everything_off_the_dive_is_filed_with_it(play) -> None:
    """The reason this matters: a link whose own input the trainer cannot read
    still has to sit beside the move it comes out of, not in the leftovers."""
    moves = {move.name: move for move in play([]).session.character.moves}
    dive = moves["Hyakki Shuu"]
    for name in ("Hyakki Gouzan", "Hyakki Goushou", "Hyakki Goujin"):
        assert moves[name].follows == dive.name, name
        assert moves[name].category == dive.category, name


def test_the_throw_off_the_dive_keeps_being_a_throw(play) -> None:
    """Gou Sai is a command grab, and the guide says so plainly enough for the
    parser to have filed it before the dive was linked up. A link only borrows
    its parent's section when nothing better is known about it."""
    moves = {move.name: move for move in play([]).session.character.moves}
    assert moves["Hyakki Gousai"].follows == "Hyakki Shuu"
    assert moves["Hyakki Gousai"].category == "throw"
