"""Button sets: how many attack buttons a game has, and what they are called.

A layout says where your fingers go; a set says what those positions mean. They
are kept apart so that adding a game with a different panel is a table entry
rather than a new layout for every keyboard arrangement.

A set is rows of buttons, laid onto the layout's rows of attack keys in order.
On the southpaw layout, whose attack keys are ``asdf`` over ``zxcv``, that gives:

    Street Fighter   asd zxc     LP MP HP over LK MK HK
    Mortal Kombat    asd zx      HP HK BL over LP LK, the modern pad mapping
    Neo Geo          asdf zxcv   A B C D, the same four on both rows
    Neo Geo slant    zx as       A B on the bottom row, C D above them
    Tekken           as zx       □ △ over ✕ ○
    Eight button     asdf zxcv   1-8

The Neo Geo has two arrangements in circulation, so which one is used is the
player's choice: :func:`arrangement` applies it.
"""

from dataclasses import dataclass

from motioninput_tui.engine.notation import Button

_B = Button


@dataclass(frozen=True, slots=True)
class ButtonSet:
    """The attack buttons of one game's panel, in rows.

    Attributes:
        key: What is saved in the config, and the pseudo-character key the
            input display is picked with.
        name: What the pickers call it.
        rows: Buttons in panel order, top row first. A row is laid onto the
            matching row of the layout's attack keys, so a row longer than the
            layout has keys for simply runs out. The same button may appear
            twice, which is how the Neo Geo gets its second row.
        note: One line on where the arrangement comes from.
    """

    key: str
    name: str
    rows: tuple[tuple[Button, ...], ...]
    note: str = ""

    @property
    def buttons(self) -> tuple[Button, ...]:
        """Every button once, in panel order."""
        seen: dict[Button, None] = {}
        for row in self.rows:
            for button in row:
                seen.setdefault(button, None)
        return tuple(seen)


STREET_FIGHTER = ButtonSet(
    key="street-fighter",
    name="Street Fighter, 6 button",
    rows=((_B.LP, _B.MP, _B.HP), (_B.LK, _B.MK, _B.HK)),
    note="Three punches over three kicks.",
)

MORTAL_KOMBAT = ButtonSet(
    key="mortal-kombat",
    name="Mortal Kombat, 5 button",
    # Not the arcade panel: this is how modern Mortal Kombat maps onto a six
    # button controller, the two heavy attacks and block on top with the light
    # pair beneath, which is why the bottom row is the short one.
    rows=((_B.HP, _B.HK, _B.BL), (_B.LP, _B.LK)),
    note="Heavy punch, heavy kick, block, with the light pair beneath.",
)

NEO_GEO = ButtonSet(
    key="neo-geo",
    name="Neo Geo, 4 button",
    rows=((_B.A, _B.B, _B.C, _B.D), (_B.A, _B.B, _B.C, _B.D)),
    note="A B C D straight across, and again on the row below.",
)

NEO_GEO_SLANT = ButtonSet(
    key="neo-geo-slant",
    name="Neo Geo, arcade slant",
    rows=((_B.C, _B.D), (_B.A, _B.B)),
    note="A B on the bottom row with C D above, as the arcade panel slants them.",
)

TEKKEN = ButtonSet(
    key="tekken",
    name="Tekken, 4 button",
    rows=((_B.SQUARE, _B.TRIANGLE), (_B.CROSS, _B.CIRCLE)),
    note="Left and right punch over left and right kick.",
)

EIGHT_BUTTON = ButtonSet(
    key="eight",
    name="Eight button",
    rows=((_B.B1, _B.B2, _B.B3, _B.B4), (_B.B5, _B.B6, _B.B7, _B.B8)),
    note="Every attack key a layout has, numbered.",
)

BUTTON_SETS: tuple[ButtonSet, ...] = (
    STREET_FIGHTER,
    MORTAL_KOMBAT,
    NEO_GEO,
    TEKKEN,
    EIGHT_BUTTON,
)
"""The sets offered in the pickers. The Neo Geo slant is not among them: it is
the same set differently arranged, and :func:`arrangement` chooses it."""

DEFAULT_SET = STREET_FIGHTER


def get_set(key: str) -> ButtonSet:
    """Look up a button set by key, falling back to the Street Fighter six."""
    for button_set in (*BUTTON_SETS, NEO_GEO_SLANT):
        if button_set.key == key:
            return button_set
    return DEFAULT_SET


def arrangement(button_set: ButtonSet, *, slanted_neo_geo: bool) -> ButtonSet:
    """The set as the player wants it arranged.

    Only the Neo Geo has a second arrangement, so this is a no-op for the rest.
    """
    if slanted_neo_geo and button_set is NEO_GEO:
        return NEO_GEO_SLANT
    return button_set
