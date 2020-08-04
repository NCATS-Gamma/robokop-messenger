"""Test answer."""
# pylint: disable=redefined-outer-name,no-name-in-module,unused-import
# ^^^ this stuff happens because of the incredible way we do pytest fixtures
from fastapi.testclient import TestClient

from messenger.server import APP
from .fixtures import empty, whatis_mondo, onestep, ebola_mondo

client = TestClient(APP)


def test_answer_empty(empty):
    """Test that answer() handles empty queries."""
    response = client.post('/answer', json={
        "message": empty
    })
    result = response.json()
    assert len(result['results']) == 1
    result = result['results'][0]
    assert isinstance(result['node_bindings'], list) and not result['node_bindings']
    assert isinstance(result['edge_bindings'], list) and not result['edge_bindings']


def test_answer_whatis(whatis_mondo):
    """Test that answer() can look up a single node."""
    response = client.post('/answer', json={
        "message": whatis_mondo
    })
    result = response.json()
    assert result['results']
    assert 'MONDO:0005737' in result['results'][0]['node_bindings'][0]['kg_id']


def test_answer_onestep(onestep):
    """Test that answer() answers one-step queries."""
    response = client.post('/answer', json={
        "message": onestep
    })
    result = response.json()
    assert result['results']
    first = result['results'][0]
    assert first['node_bindings']
    assert first['edge_bindings']


def test_ebola(ebola_mondo):
    """Test that answer() answers ebola."""
    response = client.post('/answer', json={
        "message": ebola_mondo
    })
