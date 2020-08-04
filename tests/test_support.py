"""Test Support."""
# pylint: disable=redefined-outer-name,no-name-in-module,unused-import
# ^^^ this stuff happens because of the incredible way we do pytest fixtures
from fastapi.testclient import TestClient

from messenger.server import APP
from .fixtures import yanked

client = TestClient(APP)


def test_support(yanked):
    """Test support()."""
    response = client.post('/support', json={
        "message": yanked
    })
    result = response.json()
    assert any(
        edge['type'] == 'literature_co-occurrence'
        for edge in result['knowledge_graph']['edges']
    )
