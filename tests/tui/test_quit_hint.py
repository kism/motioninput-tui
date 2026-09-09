"""ctrl+q is shown in the footer. Textual's own binding for it is hidden, so
the app re-declares it or the only quit hint is ctrl+c's second-press toast.
"""

import asyncio
from typing import TYPE_CHECKING

from textual.binding import Binding

from motioninput_tui.config import Config
from motioninput_tui.tui import MotionInputApp

if TYPE_CHECKING:
    from pathlib import Path


def test_ctrl_q_is_declared_visible() -> None:
    """Textual's own ctrl+q is show=False; the app has to re-declare it."""
    quit_bindings = [
        binding for binding in MotionInputApp.BINDINGS if isinstance(binding, Binding) and binding.key == "ctrl+q"
    ]
    assert quit_bindings == [Binding("ctrl+q", "quit", "Quit", priority=True)]


def test_ctrl_q_quits(tmp_path: Path) -> None:
    async def session() -> int | None:
        config = Config(game="usfiv", character="ryu", layout="keyboard-left", path=tmp_path / "config.json")
        app = MotionInputApp(config, key_release=False, skip_setup=True)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            await pilot.press("ctrl+q")
            await pilot.pause()
        return app.return_code

    assert asyncio.run(session()) == 0
