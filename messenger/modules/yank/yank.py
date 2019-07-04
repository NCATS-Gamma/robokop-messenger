"""Yank."""
from neo4j import GraphDatabase, basic_auth
from messenger.shared.message_state import kgraph_is_local
from messenger.cypher_adapter import Node, Edge, Graph
from messenger.shared.util import random_string
from .qgraph_compiler import cypher_query_answer_map


def KGraph(kgraph):
    """Return a LocalKGraph or RemoteKGraph, depending on the structure of `kgraph`."""
    # TODO: rigorously check against json schema
    if "edges" in kgraph:
        return LocalKGraph(kgraph)
    else:
        return RemoteKGraph(kgraph)


class RemoteKGraph:
    """Context manager for persistent remote KGraph."""

    def __init__(self, kgraph):
        """Initialize context manager."""
        # get Neo4j connection
        self.driver = GraphDatabase.driver(
            kgraph["url"],
            auth=basic_auth(
                kgraph["credentials"]["username"],
                kgraph["credentials"]["password"]
            ),
        )

    def __enter__(self):
        """Enter context."""
        return self.driver

    def __exit__(self, type, value, traceback):
        """Exit context."""
        pass


class LocalKGraph:
    """Context manager for temporary cypher-able KGraph."""

    def __init__(self, kgraph):
        """Initialize context manager."""
        self.kgraph = kgraph
        self.driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=basic_auth("neo4j", "pword")
        )
        self.uid = random_string()

    def __enter__(self):
        """Enter context."""
        neo4j_graph = Graph("kg", self.driver)
        nodes = {}
        for node in self.kgraph["nodes"]:
            node_type = node['type']
            if isinstance(node_type, str):
                node_type = [node_type]
            node_id = node['id'].replace('"', '\\"')
            nodes[node["id"]] = Node(
                labels=[self.uid] + node_type,
                properties={
                    # "name": node["name"],
                    "id": node_id
                },
            )
        edges = {}
        for edge in self.kgraph["edges"]:
            edges[edge["id"]] = Edge(
                nodes[edge["source_id"]],
                edge["type"],
                nodes[edge["target_id"]],
                properties={"id": edge["id"]},
            )

        for node in nodes.values():
            neo4j_graph.add_node(node)

        for edge in edges.values():
            neo4j_graph.add_edge(edge)

        neo4j_graph.commit()
        return self.driver

    def __exit__(self, type, value, traceback):
        """Exit context."""
        with self.driver.session() as session:
            session.run(f"MATCH (n:{self.uid}) DETACH DELETE n")


def query(message, max_connectivity=0):
    """Fetch answers to question."""
    with KGraph(message["knowledge_graph"]) as driver:
        message = query_neo4j(message, driver, max_connectivity=max_connectivity)
    return message


def query_neo4j(message, driver, max_connectivity):
    """Query Neo4j for answers to question."""
    qgraph = message["query_graph"]
    # get all answer maps relevant to the question from the knowledge graph
    answers = []
    options = {"limit": 1000000, "skip": 0, "max_connectivity": max_connectivity}

    while True:
        query_string = cypher_query_answer_map(qgraph, options=options)

        with driver.session() as session:
            result = session.run(query_string)

        these_answers = [{
            "node_bindings": r["nodes"],
            "edge_bindings": r["edges"]
        } for r in result]

        options["skip"] += options["limit"]
        answers.extend(these_answers)

        if len(these_answers) < options["limit"]:
            # If this batch is smaller then the page size,
            # it must be the last page.
            break
        elif len(answers) >= options["limit"]:
            # Maximum number of potential answers reached.
            break

    message["results"] = answers
    return message
