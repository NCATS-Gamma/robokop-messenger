"""Answer."""
import copy
import logging
import os
from neo4j import GraphDatabase, basic_auth
from messenger.shared.message_state import kgraph_is_local
from messenger.cypher_adapter import Node, Edge, Graph
from messenger.shared.util import random_string
from messenger.shared.neo4j import dump_kg
from messenger.shared.qgraph_compiler import cypher_query_answer_map

logger = logging.getLogger(__name__)


def KGraph(message):
    """Return a LocalKGraph or RemoteKGraph, depending on the structure of `kgraph`."""
    if 'knowledge_graph' not in message:
        message['knowledge_graph'] = {
            'url': 'bolt://robokopdb2.renci.org:7687',
            'credentials': {
                'username': 'neo4j',
                'password': 'ncatsgamma',
            },
        }
    # TODO: rigorously check against json schema
    if "edges" in message['knowledge_graph']:
        return LocalKGraph(message)
    else:
        return RemoteKGraph(message)


class RemoteKGraph:
    """Context manager for persistent remote KGraph."""

    def __init__(self, message):
        """Initialize context manager."""
        # get Neo4j connection
        kgraph = message['knowledge_graph']
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

    def __init__(self, message):
        """Initialize context manager."""
        self.driver = GraphDatabase.driver(
            f"bolt://{os.environ['LOCAL_NEO4J_HOST']}:7687",
            auth=basic_auth("neo4j", "pword")
        )
        self.uid = random_string()
        self.kgraph = message['knowledge_graph']
        self.qgraph = message['query_graph']

    def add_uid(self):
        """Add uid to node labels."""
        # add uid to kgraph nodes
        nodes = []
        for node in self.kgraph['nodes']:
            node_type = node.get('type', '')
            if isinstance(node_type, str):
                node_type = [node_type]
            node_type.append(self.uid)
            node['type'] = node_type
            nodes.append(node)
        self.kgraph['nodes'] = nodes

        # add uid to qgraph nodes
        nodes = []
        for node in self.qgraph['nodes']:
            node_type = node.get('type', '')
            if isinstance(node_type, str):
                node_type = [node_type]
            node_type.append(self.uid)
            node['type'] = node_type
            nodes.append(node)
        self.qgraph['nodes'] = nodes

    def remove_uid(self):
        """Remove uid labels from nodes."""
        # remove uid from kgraph nodes
        for node in self.kgraph['nodes']:
            node['type'].remove(self.uid)

        # remove uid from qgraph nodes
        for node in self.qgraph['nodes']:
            node['type'].remove(self.uid)

    def __enter__(self):
        """Enter context."""
        self.add_uid()
        dump_kg(self.driver, self.kgraph)
        return self.driver

    def __exit__(self, type, value, traceback):
        """Exit context."""
        with self.driver.session() as session:
            session.run(f"MATCH (n:{self.uid}) DETACH DELETE n")
        self.remove_uid()


def query(message, *, max_connectivity=-1):
    """Fetch answers to question."""
    message = copy.deepcopy(message)
    with KGraph(message) as driver:
        message = query_neo4j(message, driver, max_connectivity=max_connectivity)
    return message


def query_neo4j(message, driver, max_connectivity=-1):
    """Query Neo4j for answers to question."""
    qgraph = message["query_graph"]
    # get all answer maps relevant to the question from the knowledge graph
    answers = []
    relationship_id = message['knowledge_graph'].get('relationship_id', 'property')
    options = {
        "limit": 1000000,
        "skip": 0,
        "max_connectivity": max_connectivity,
        "relationship_id": relationship_id,
    }

    while True:
        query_string = cypher_query_answer_map(qgraph, **options)

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
