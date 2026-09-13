"""Global settings: the player's own preferences, above any game's rules.

A :class:`~motioninput_tui.engine.ruleset.Ruleset` says how one game reads
inputs; these are the player's, whichever game is selected. They are chosen in
the settings pane of the setup screen and saved with the rest of the config.

Each one is a boolean attribute of :class:`~motioninput_tui.config.Config`, so
the pane can read and write them by name without knowing what any of them mean.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from motioninput_tui.config import Config


@dataclass(frozen=True, slots=True)
class Setting:
    """One on/off preference and how to present it.

    Attributes:
        attribute: The boolean attribute of ``Config`` holding it.
        name: What the settings pane calls it.
        detail: The line shown under the pane while it is highlighted.
    """

    attribute: str
    name: str
    detail: str

    def read(self, config: Config) -> bool:
        """Whether this setting is currently on."""
        return bool(getattr(config, self.attribute))


SETTINGS: tuple[Setting, ...] = (
    Setting(
        attribute="neo_geo_slant",
        name="Neo Geo slant",
        detail="Neo Geo's four buttons as the arcade slants them, A B below C D. Off puts A B C D across.",
    ),
    Setting(
        attribute="loose_buffer",
        name="Loose buffer",
        detail="Inputs are not spent when a move comes out, so one motion can feed several. Not how the games behave.",
    ),
)


def current(config: Config) -> dict[str, bool]:
    """Every setting's value, keyed by attribute, for handing to a screen."""
    return {setting.attribute: setting.read(config) for setting in SETTINGS}
