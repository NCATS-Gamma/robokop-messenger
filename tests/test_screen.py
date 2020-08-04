"""Test screening."""
# pylint: disable=redefined-outer-name,no-name-in-module,unused-import
# ^^^ this stuff happens because of the incredible way we do pytest fixtures
from fastapi.testclient import TestClient

from messenger.server import APP
from .fixtures import weighted2

client = TestClient(APP)


def test_screen(weighted2):
    """Test that screen() runs without errors."""
    response = client.post('/score', json={
        "message": weighted2
    })
    response = client.post('/screen?max_result=3', json={
        "message": response.json()
    })
    result = response.json()
    assert len(result['results']) == 3
