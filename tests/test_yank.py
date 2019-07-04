"""Test yank."""
# pylint: disable=redefined-outer-name,no-name-in-module,unused-import
# ^^^ this stuff happens because of the incredible way we do pytest fixtures
from messenger.modules.yank import query as yank
from .fixtures import empty, whatis_mondo, onestep, ebola_mondo


def test_yank_empty(empty):
    """Test that yank() handles empty queries."""
    result = yank(empty)
    assert len(result['results']) == 1
    result = result['results'][0]
    assert isinstance(result['node_bindings'], list) and not result['node_bindings']
    assert isinstance(result['edge_bindings'], list) and not result['edge_bindings']


def test_yank_whatis(whatis_mondo):
    """Test that yank() can look up a single node."""
    result = yank(whatis_mondo)
    assert result['results']
    assert 'MONDO:0005737' in result['results'][0]['node_bindings'][0]['kid']


def test_yank_onestep(onestep):
    """Test that yank() answers one-step queries."""
    result = yank(onestep)
    assert result['results']
    first = result['results'][0]
    assert first['node_bindings']
    assert first['edge_bindings']

def test_ebola(ebola_mondo):
    """Test that yank() answers ebola."""
    result = yank(ebola_mondo)
