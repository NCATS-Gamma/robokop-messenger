"""Answer."""
import copy
import logging
import os
from neo4j import GraphDatabase, basic_auth
from messenger.shared.util import random_string
from messenger.shared.neo4j import dump_kg
from messenger.shared.qgraph_compiler import cypher_query_answer_map
from messenger.modules.answer import KGraph

logger = logging.getLogger(__name__)


def query(message, *, threshold=0.5):
    """Fetch answers to question."""
    message = copy.deepcopy(message)
    with KGraph(message) as driver:
        message = query_neo4j(
            message,
            driver,
            threshold,
        )
    return message


def query_neo4j(message, driver, threshold):
    """Query Neo4j for query nodes similar to anchor node.
    
    {
        "message": {
            "query_graph": {
                "edges": [
                    {
                        "id":"e00",
                        "source_id":"n00",
                        "target_id":"n02",
                        "by":"n01",
                        "type":"similarity"
                    }
                ],
                "nodes": [
                    {
                        "curie": "MONDO:0005737",
                        "id": "n00",
                        "type":"disease"
                    },
                    {
                        "type": "phenotypic_feature",
                        "id": "n01"
                    },
                    {
                        "type": "disease",
                        "id": "n02"
                    }
                ]
            }
        },
        "options": {
            "threshold": 0.5
        }
    }"""
    relationship_id = message['knowledge_graph'].get('relationship_id', 'property')
    options = {
        "relationship_id": relationship_id,
    }

    qgraph = message["query_graph"]
    sim_edges = [edge for edge in qgraph['edges'] if edge['type'] == 'similarity']
    qnode_map = {
        node['id']: node
        for node in qgraph['nodes']
    }

    answers = []
    for edge in sim_edges:
        node0 = qnode_map[edge['source_id']]
        node1 = qnode_map[edge['target_id']]
        by_node_set = qnode_map[edge['by']]
        if 'curie' in node0:
            anchor_node = node0
            query_node = node1
        else:
            anchor_node = node1
            query_node = node0
        query_string = f"""MATCH (query:{anchor_node['type']} {{id:"{anchor_node['curie']}"}})--(b:{by_node_set['type']})
            WITH query, count(*) as n1, collect(b) as bs
            UNWIND bs as b
            MATCH (b)--(result:{query_node['type']})
            WITH result, collect(DISTINCT b.id) as intersection, n1
            MATCH (result)--(b:{by_node_set['type']})
            WITH result.id as result, ((1.0 * size(intersection))/(n1 + count(DISTINCT b.id) - size(intersection))) AS jaccard, intersection
            WHERE jaccard > {threshold}
            RETURN result, intersection, jaccard ORDER BY jaccard DESC"""
        logger.debug(query_string)

        result = driver.run(query_string)

        answers.extend([{
            "node_bindings": [
                {
                    'qg_id': anchor_node['id'],
                    'kg_id': anchor_node['curie'],
                },
                {
                    'qg_id': by_node_set['id'],
                    'kg_id': r['intersection'],
                },
                {
                    'qg_id': query_node['id'],
                    'kg_id': r['result'],
                },
            ],
            "edge_bindings": [],
            "score": r['jaccard'],
        } for r in result])

    message["results"] = answers
    return message
