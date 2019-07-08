#! /usr/bin/env python
"""Set up Neo4j."""

import json
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
with open('tests/data/ebola_kg.json', 'r') as f:
    kgraph = json.load(f)
clear(driver)
dump_kg(driver, kgraph, with_props=True)
