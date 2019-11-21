#! /usr/bin/env python
"""Set up Neo4j."""

from collections import namedtuple
from itertools import product
import json
import os
import re
import uuid
from dotenv import load_dotenv
from neo4j import GraphDatabase, basic_auth
from messenger.shared.neo4j import dump_kg, clear, Neo4jDatabase

file_path = os.path.dirname(os.path.realpath(__file__))
dotenv_path = os.path.abspath(os.path.join(file_path, '..', '.env'))
load_dotenv(dotenv_path=dotenv_path)

Edge = namedtuple('Edge', ['source_id', 'target_id'])
Node = namedtuple('Node', ['id', 'type'])


class Graph():
    """Graph class."""

    def __init__(self, graph=None):
        """Initialize graph."""
        if graph is None:
            self.graph = {
                'nodes': [],
                'edges': [],
            }
        else:
            self.graph = graph

    def add_node(self, node, type_=None):
        """Add node to graph."""
        if type_ is None:
            type_ = []
        elif isinstance(type_, str):
            type_ = [type_]
        type_.append('test')
        self.graph['nodes'].append(Node(node, type_))

    def add_edge(self, source_id, target_id):
        """Add edge to graph."""
        self.graph['edges'].append(Edge(source_id, target_id))

    def connect(self, pattern1, pattern2):
        """Connect all nodes matching pattern1 to all nodes matching pattern2."""
        for node1, node2 in product(self.graph['nodes'], repeat=2):
            if (
                    re.fullmatch(pattern1, node1.id) and
                    re.fullmatch(pattern2, node2.id)
            ):
                self.add_edge(
                    node1.id,
                    node2.id,
                )

    def to_json(self):
        """Generate JSON representation of graph."""
        return {
            'nodes': [node._asdict() for node in self.graph['nodes']],
            'edges': [{
                'id': str(uuid.uuid4()),
                'type': 'interacts_with',
                'source_id': edge[0],
                'target_id': edge[1],
            } for edge in self.graph['edges']],
        }

    def __str__(self):
        """Generate string representation of graph."""
        return str(json.dumps(
            self.to_json(),
            indent=4,
            ensure_ascii=False,
        ))


def big_set():
    """Generate graph to test the effect of set size."""
    g = Graph()
    g.add_node('start', 'A')
    g.add_node('small0', 'B')
    g.add_node('big0', 'B')
    for idx in range(10):
        g.add_node(f'bigset{idx:02d}', 'C')
    for idx in range(3):
        g.add_node(f'smallset{idx:02d}', 'C')
    g.add_node('small1', 'D')
    g.add_node('big1', 'D')
    g.add_node('end', 'E')
    g.connect('start', 'small0')
    g.connect('start', 'big0')
    g.connect('small0', 'smallset.*')
    g.connect('small1', 'smallset.*')
    g.connect('big0', 'bigset.*')
    g.connect('big1', 'bigset.*')
    g.add_edge('small1', 'end')
    g.add_edge('big1', 'end')
    return g


url = f'bolt://{os.environ["NEO4J_HOST"]}:{os.environ["NEO4J_BOLT_PORT"]}'
driver = Neo4jDatabase(
    url=url,
    credentials={
        'username': os.environ['NEO4J_USER'],
        'password': os.environ['NEO4J_PASSWORD'],
    },
)
with open(os.path.join(os.environ['ROBOKOP_HOME'], 'robokop-messenger', 'tests', 'data', 'ebola_kg.json'), 'r') as f:
    kgraph = json.load(f)
for node in kgraph['nodes']:
    node['type'].append('test')
clear(driver)
dump_kg(driver, kgraph, with_props=True)

dump_kg(driver, big_set().to_json())

statement = "MATCH ()-[e]-() RETURN DISTINCT type(e) as predicate"
result = driver.run(statement)
predicates = [record['predicate'] for record in result]
predicates_string = ', '.join(f"'{predicate}'" for predicate in predicates)
statement = f"""CALL db.index.fulltext.createRelationshipIndex(
    'edge_id_index',
    [{predicates_string}],
    ['id'],
    {{analyzer: 'keyword'}}
)"""
driver.run(statement)
