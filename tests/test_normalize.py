"""Test normalize."""
# pylint: disable=redefined-outer-name,no-name-in-module,unused-import
# ^^^ this stuff happens because of the incredible way we do pytest fixtures
from fastapi.testclient import TestClient

from messenger.server import APP
from .fixtures import nonsense_curie, whatis_doid

client = TestClient(APP)


def test_normalize_nonsense(nonsense_curie):
    """Test that normalize() returns the input for curies that cannot be normalized."""
    response = client.post('/normalize', json={
        "message": nonsense_curie
    })
    result = response.json()
    assert result['query_graph']['nodes'][0]['curie'] == ['x:NONSENSE']


def test_normalize_ebola(whatis_doid):
    """Test that normalize() maps DOIDs to MONDO ids."""
    response = client.post('/normalize', json={
        "message": whatis_doid
    })
    result = response.json()
    assert result['query_graph']['nodes'][0]['curie'] == ['MONDO:0005737']
