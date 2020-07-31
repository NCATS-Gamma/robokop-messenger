"""Test server."""

from fastapi.testclient import TestClient

from messenger.server import APP
from .fixtures import empty

client = TestClient(APP)


def test_empty(empty):
    """Test server with empty message."""
    response = client.post('/answer', json=empty.dict())
    assert response.status_code == 200
