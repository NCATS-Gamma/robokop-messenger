"""Test quotes."""
# pylint: disable=redefined-outer-name,no-name-in-module,unused-import
# ^^^ this stuff happens because of the incredible way we do pytest fixtures
import json

from messenger.modules.yank import query as yank
from messenger.modules.normalize import query as normalize
from .fixtures import quotes_local


def test_quotes(quotes_local):
    """Test handling quotes in node id."""
    yanked = yank(quotes_local)
    assert yanked['results'][0]['node_bindings'][1]['kid'] == 'gene1\">'
