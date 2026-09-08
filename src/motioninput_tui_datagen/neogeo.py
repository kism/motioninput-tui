"""Putting a parsed motion back onto the Neo Geo's four-button panel.

``normalise`` reads one dialect, the Street Fighter six, so an SNK guide's
commands are translated into it for parsing and the resulting button
requirement is mapped back here. The recogniser matches ``Button`` identity,
not punch/kick family, so without this every KoF move would want an SF button
the Neo Geo layout never produces.

Shared by the KoF '98 and KoF 2001 parsers, which read very different dialects
but land on the same panel.
"""

from dataclasses import replace
from typing import TYPE_CHECKING

from motioninput_tui.engine.notation import ALL_BUTTONS, KICKS, PUNCHES, Button, ButtonRequirement

if TYPE_CHECKING:
    from motioninput_tui.engine.motions import MotionSpec

NEO_PUNCHES = frozenset({Button.A, Button.C})
NEO_KICKS = frozenset({Button.B, Button.D})

_TO_NEO = {
    Button.LP: Button.A,
    Button.MP: Button.A,
    Button.HP: Button.C,
    Button.LK: Button.B,
    Button.MK: Button.B,
    Button.HK: Button.D,
}
_NEO_ORDER = (Button.A, Button.B, Button.C, Button.D)

TO_SHORTHAND = {"A": "LP", "B": "LK", "C": "HP", "D": "HK", "P": "any punch", "K": "any kick"}
"""Neo Geo button letters in the dialect ``normalise`` reads. A and B are the
light punch and kick, C and D the heavy pair."""


def to_neo_panel(motion: MotionSpec, command: str) -> MotionSpec:
    """Put a motion's button requirement back onto the Neo Geo's A B C D."""
    return replace(motion, buttons=neo_buttons(motion.buttons), notation=command.strip())


def neo_buttons(requirement: ButtonRequirement) -> ButtonRequirement:
    """The same requirement expressed in Neo Geo buttons."""
    count = requirement.count
    if requirement.allowed == PUNCHES:
        return ButtonRequirement(NEO_PUNCHES, count, "P" * count)
    if requirement.allowed == KICKS:
        return ButtonRequirement(NEO_KICKS, count, "K" * count)
    if requirement.allowed == ALL_BUTTONS:
        return ButtonRequirement(NEO_PUNCHES | NEO_KICKS, count, "any button")
    mapped = frozenset(_TO_NEO.get(button, button) for button in requirement.allowed)
    names = [button.value for button in _NEO_ORDER if button in mapped]
    return ButtonRequirement(mapped, count, ("+" if count >= len(names) else "/").join(names))
