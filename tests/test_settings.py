"""The global settings: each a boolean on the config, which is how the pane reads and writes them."""

from motioninput_tui.config import Config
from motioninput_tui.engine.recognizer import BufferPolicy
from motioninput_tui.settings import SETTINGS, current


def test_loose_buffer_reads_and_writes_the_policy() -> None:
    """The pane sees every setting as a boolean, including the one that is an enum."""
    config = Config()
    assert config.loose_buffer is False
    config.loose_buffer = True
    assert config.buffer_policy is BufferPolicy.LOOSE
    config.loose_buffer = False
    assert config.buffer_policy is BufferPolicy.CONSUME


def test_every_setting_is_a_boolean_on_the_config() -> None:
    """The settings pane writes them back by name, so they have to be there."""
    values = current(Config())
    assert set(values) == {setting.attribute for setting in SETTINGS}
    assert all(isinstance(value, bool) for value in values.values())
