"""Test ranking of big sets."""
# pylint: disable=redefined-outer-name,no-name-in-module,unused-import
# ^^^ this stuff happens because of the incredible way we do pytest fixtures
from fastapi.testclient import TestClient

from messenger.server import APP
from .fixtures import bigset

client = TestClient(APP)


def test_answer_bigset(bigset):
    """Test that answer() handles empty queries."""
    response = client.post('/answer', json={
        "message": bigset
    })
    response = client.post('/weight_novelty', json={
        "message": response.json()
    })
    response = client.post('/score', json={
        "message": response.json()
    })


def test_score_leafset(bigset):
    """Test that answer() handles empty queries."""
    bigset['query_graph']['nodes'] = bigset['query_graph']['nodes'][:3]
    bigset['query_graph']['edges'] = bigset['query_graph']['edges'][:2]
    response = client.post('/answer', json={
        "message": bigset
    })
    response = client.post('/weight_correctness', json={
        "message": response.json()
    })
    response = client.post('/score', json={
        "message": response.json()
    })
