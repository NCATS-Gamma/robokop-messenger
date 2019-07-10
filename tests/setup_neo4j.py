#! /usr/bin/env python
"""Set up Neo4j."""

import json
import os
from neo4j import GraphDatabase, basic_auth
from messenger.shared.neo4j import dump_kg, clear

url = 'bolt://localhost:7687'
driver = GraphDatabase.driver(
    url,
    auth=basic_auth(
        'neo4j',
        'pword'
    ),
)
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'ebola_kg.json'), 'r') as f:
    kgraph = json.load(f)
clear(driver)
dump_kg(driver, kgraph, with_props=True)

predicates = set(edge['type'] for edge in kgraph['edges'])
predicates_string = ', '.join(f"'{predicate}'" for predicate in predicates)
statement = f"""CALL db.index.fulltext.createRelationshipIndex(
    'edge_id_index',
    [{predicates_string}],
    ['id'],
    {{analyzer: 'keyword'}}
)"""
with driver.session() as session:
    session.run(statement)
