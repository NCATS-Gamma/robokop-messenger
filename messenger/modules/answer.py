"""Answer."""
import logging
import os

from reasoner.cypher import get_query

from messenger.shared.neo4j import Neo4jDatabase

logger = logging.getLogger(__name__)

NEO4J_HOST = os.environ.get('NEO4J_HOST', 'localhost')
NEO4J_BOLT_PORT = os.environ.get('NEO4J_BOLT_PORT', '7687')
NEO4J_USER = os.environ.get('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD', 'pword')


def query(message, *, max_connectivity=-1):
    """Fetch answers to question."""
    message = copy.deepcopy(message)
    neo4j = Neo4jDatabase(
        url=f'bolt://{NEO4J_HOST}:{NEO4J_BOLT_PORT}',
        credentials={
            'username': NEO4J_USER,
            'password': NEO4J_PASSWORD,
        },
    )
    qgraph = message['query_graph']
    cypher = get_query(
        qgraph,
        max_connectivity=max_connectivity,
    )
    message = neo4j.run(cypher)[0]
    message['query_graph'] = qgraph
    return message
