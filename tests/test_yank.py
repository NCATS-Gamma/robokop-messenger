"""Test yank."""
from tests.fixtures import answered
from messenger.modules.yank import query as yank


def test_yank(answered):
    """Test yank()."""
    yank(answered)
