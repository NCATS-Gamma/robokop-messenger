"""Test Neo4j."""
# pylint: disable=redefined-outer-name,no-name-in-module,unused-import
# ^^^ this stuff happens because of the incredible way we do pytest fixtures
import json
import os
import pytest
from messenger.shared.neo4j import get_edge_properties, get_node_properties


def test_yank_edges():
    """Test yanking edges from the KG."""
    options = {
        "url": f"bolt://{os.environ['NEO4J_HOST']}:{os.environ['NEO4J_PORT']}",
        "credentials": {
            "username": os.environ['NEO4J_USER'],
            "password": os.environ['NEO4J_PASSWORD'],
        },
    }
    edge_id = '18557484'
    edges = get_edge_properties([edge_id], **options)
    assert len(edges) == 1
    assert edges[0]['id'] == edge_id


def test_fail_yank():
    """Test yanking nodes/edges from the KG."""
    options = {
        "url": f"bolt://{os.environ['NEO4J_HOST']}:{os.environ['NEO4J_PORT']}",
        "credentials": {
            "username": os.environ['NEO4J_USER'],
            "password": os.environ['NEO4J_PASSWORD'],
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
