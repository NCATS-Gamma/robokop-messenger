"""Yank relevant local knowledge graph from Neo4j."""
from messenger.shared.neo4j import edges_from_answers, nodes_from_answers
from messenger.shared.message_state import kgraph_is_local


def query(message, *, bypass_index=False):
    """Copy relevant portions of remote knowledge graph into local knowledge graph."""
    if kgraph_is_local(message):
        return message
    nodes = nodes_from_answers(message)
    edges = edges_from_answers(message, bypass_index=bypass_index)

    kg = {
        'nodes': nodes,
        'edges': edges
    }
    message['knowledge_graph'] = kg

    return message
