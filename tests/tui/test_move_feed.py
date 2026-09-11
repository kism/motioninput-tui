"""The feed's rendering of a two-phase move's follow-through."""

from rich.text import Text

from motioninput_tui.engine.notation import KICKS
from motioninput_tui.engine.recognizer import FollowUp, FollowUpStatus
from motioninput_tui.tui.widgets.move_feed import append_follow_up


def _render(status: FollowUpStatus, got: int, *, newest: bool, rhythm: bool = True) -> str:
    follow_up = FollowUp(
        button_label="P", needed=3, rhythm=rhythm, buttons=KICKS, deadline_ms=0, got=got, status=status
    )
    text = Text()
    append_follow_up(text, follow_up, newest=newest)
    return text.plain


def test_pending_prompts_for_the_taps() -> None:
    assert _render(FollowUpStatus.PENDING, 1, newest=True) == "●○○  tap P!"


def test_pending_mash_says_mash() -> None:
    assert _render(FollowUpStatus.PENDING, 0, newest=True, rhythm=False) == "○○○  mash P!"


def test_complete_shows_all_ticks() -> None:
    assert _render(FollowUpStatus.COMPLETE, 3, newest=True) == "✓✓✓"


def test_missed_shows_how_far_it_got() -> None:
    assert _render(FollowUpStatus.MISSED, 2, newest=True) == "✓✓·  missed"


def test_older_entries_are_compact() -> None:
    assert _render(FollowUpStatus.PENDING, 1, newest=False) == "●○○"
