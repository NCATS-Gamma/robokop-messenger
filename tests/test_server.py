"""Test server."""
import os
import pytest
from messenger.server import app as flask_app
from fixtures import empty


@pytest.fixture
def client():
    """Generate test server."""
    flask_app.app.config['TESTING'] = True
    yield flask_app.app.test_client()


def test_empty(client, empty):
    """Test server with empty message."""
    request = {
        'message': empty,
        'options': {}
    }
    response = client.post('/answer', json=request)
    assert response.status_code == 200
