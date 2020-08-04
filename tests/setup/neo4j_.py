"""Neo4j utils for test setup."""
from copy import deepcopy

from tests.setup.cypher_adapter import Node, Edge, Graph


def clear(driver):
    """Clear nodes and edges from Neo4j."""
    driver.run(f"MATCH (n) DETACH DELETE n")


def escape_quotes(string):
    """Escape double quotes in string."""
    return string.replace('"', '\\"')


def dump_kg(driver, kgraph, with_props=False):
    """Dump knowledge graph into Neo4j database."""
    neo4j_graph = Graph("kg", driver)
    kgraph = deepcopy(kgraph)
    nodes = {}
    for node in kgraph["nodes"]:
        node_type = node.pop('type')
        if isinstance(node_type, str):
            node_type = [node_type]
        node_type.append('named_thing')
        node_id = escape_quotes(node.pop('id'))
        properties = {
            "id": node_id
        }
        if with_props:
            properties.update(**node)
        nodes[node_id] = Node(
            labels=node_type,
            properties=properties,
        )
    edges = {}
    for edge in kgraph["edges"]:
        edge_id = edge.pop('id')
        source_id = escape_quotes(edge.pop('source_id'))
        target_id = escape_quotes(edge.pop('target_id'))
        edge_type = edge.pop('type')
        if edge_type == 'literature_co-occurrence':
            continue
        properties = {"id": edge_id}
        if with_props:
            properties.update(**edge)
        edges[edge_id] = Edge(
            nodes[source_id],
            edge_type,
            nodes[target_id],
            properties=properties,
        )

    for node in nodes.values():
        neo4j_graph.add_node(node)

    for edge in edges.values():
        neo4j_graph.add_edge(edge)

    neo4j_graph.commit()
    return
