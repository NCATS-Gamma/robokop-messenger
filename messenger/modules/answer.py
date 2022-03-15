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
    import re
    
    m = re.search(r"\-[`[a-zA-Z0-9:]*`:[a-zA-Z0-9:_]*\]-", cypher)
    if m :
        predicate = m.group(0)
        logger.info(predicate)
        predicate = predicate[0]
        new_predicate_parts = predicate.split(':')
        actual_predicate = "`" + new_predicate_parts[1].replace(']-', '') + "`"
        new_predicate = new_predicate_parts[0] + ":" + actual_predicate + "`]-" 
        logger.info(f"old cypher:{cypher}")
        cypher = cypher.replace(predicate, new_predicate)
        logger.info(f"new cypher: {cypher}")  
    
    message = (await neo4j.arun(cypher))[0]
    message['query_graph'] = qgraph
    return Message(**message)
