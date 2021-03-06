"""Test Neo4j."""
# pylint: disable=redefined-outer-name,no-name-in-module,unused-import
# ^^^ this stuff happens because of the incredible way we do pytest fixtures
import json
import os
import pytest
from .setup.neo4j_ import get_edge_properties, get_node_properties

NEO4J_URL = os.environ.get('NEO4J_URL', 'http://localhost:7474')
NEO4J_USER = os.environ.get('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD', 'pword')


def test_yank_edges():
    """Test yanking edges from the KG."""
    options = {
        "url": NEO4J_URL,
        "credentials": {
            "username": NEO4J_USER,
            "password": NEO4J_PASSWORD,
        },
    }
    edge_id = '18557484'
    edges = get_edge_properties([edge_id], **options)
    assert len(edges) == 1
    assert edges[0]['id'] == edge_id


def test_fail_yank():
    """Test yanking nodes/edges from the KG."""
    options = {
        "url": NEO4J_URL,
        "credentials": {
            "username": NEO4J_USER,
            "password": NEO4J_PASSWORD,
        },
    }
    edge_ids = [
        '18557484',
        'nope',
    ]
    with pytest.raises(RuntimeError):
        get_edge_properties(edge_ids, **options)

    node_ids = [
        'MONDO:0005737',
        'nope',
    ]
    with pytest.raises(RuntimeError):
        get_node_properties(node_ids, **options)
