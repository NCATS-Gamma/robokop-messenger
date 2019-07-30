"""Test yank."""
from fixtures import answered
from messenger.modules.yank import query as yank


def test_yank(answered):
    """Test yank()."""
    yank(answered)
