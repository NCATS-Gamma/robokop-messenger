"""Answer."""
import logging
import os

from reasoner.cypher import get_query
from reasoner_pydantic import Request, Message

from messenger.shared.neo4j_ import Neo4jDatabase

logger = logging.getLogger(__name__)

NEO4J_URL = os.environ.get('NEO4J_URL', 'http://localhost:7474')
NEO4J_USER = os.environ.get('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD', 'pword')


async def query(request: Request, *, max_connectivity: int = -1) -> Message:
    """Fetch answers to question."""
    message = request.message.dict()
    neo4j = Neo4jDatabase(
        url=NEO4J_URL,
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
    message = (await neo4j.arun(cypher))[0]
    message['query_graph'] = qgraph
    return Message(**message)
