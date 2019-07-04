"""Cypher writing library.

adapted from:
https://github.com/RedisGraph/redisgraph-py/blob/master/redisgraph/client.py
"""

import random
import string


def random_string(length=10):
    """Return a random N-character-long string."""
    return ''.join(random.choice(string.ascii_lowercase) for x in range(length))


def quote_string(prop):
    """Wrap given prop with quotes in case prop is a string.

    RedisGraph strings must be quoted.
    """
    if not isinstance(prop, str):
        return prop

    if prop[0] != '"':
        prop = '"' + prop

    if prop[-1] != '"':
        prop = prop + '"'

    return prop


class Node(object):
    """A node within the graph."""

    def __init__(self, node_id=None, alias=None, properties=None, **kwargs):
        """Create a new node."""
        self.id = node_id
        self.alias = alias
        if 'labels' in kwargs:
            self.labels = kwargs.pop('labels')
        elif 'label' in kwargs:
            self.labels = [kwargs.pop('label')]
        else:
            self.labels = []
        self.properties = {} or properties

    def __str__(self):
        """Generate string representation of node."""
        res = '('
        if self.alias:
            res += self.alias
        for label in self.labels:
            res += ':' + label
        if self.properties:
            props = ','.join(key + ':' + str(quote_string(val)) for key, val in self.properties.items())
            res += '{' + props + '}'
        res += ')'

        return res


class Edge(object):
    """An edge connecting two nodes."""

    def __init__(self, src_node, relation, dest_node, properties=None):
        """Create a new edge."""
        assert src_node is not None and dest_node is not None

        self.relation = '' or relation
        self.properties = {} or properties
        self.src_node = src_node
        self.dest_node = dest_node

    def __str__(self):
        """Generate string representation of edge."""
        # Source node.
        res = '(' + self.src_node.alias + ')'

        # Edge
        res += "-["
        if self.relation:
            res += ":" + self.relation
        if self.properties:
            props = ','.join(key + ':' + str(quote_string(val)) for key, val in self.properties.items())
            res += '{' + props + '}'
        res += ']->'

        # Dest node.
        res += '(' + self.dest_node.alias + ')'

        return res


class Graph(object):
    """Graph, collection of nodes and edges."""

    def __init__(self, name, neo4j_driver):
        """Create a new graph."""
        self.name = name
        self.neo4j_driver = neo4j_driver
        self.nodes = {}
        self.edges = []

    def add_node(self, node):
        """Add a node to the graph."""
        if node.alias is None:
            node.alias = random_string()
        self.nodes[node.alias] = node

    def add_edge(self, edge):
        """Add an edge to the graph."""
        # Make sure edge both ends are in the graph
        assert self.nodes[edge.src_node.alias] is not None and self.nodes[edge.dest_node.alias] is not None
        self.edges.append(edge)

    def commit(self):
        """Create entire graph."""
        query = 'CREATE '
        for _, node in self.nodes.items():
            query += str(node) + ','

        for edge in self.edges:
            query += str(edge) + ','

        # Discard leading comma.
        if query[-1] == ',':
            query = query[:-1]

        return self.query(query)

    def query(self, q):
        """Execute a query against the graph."""
        with self.neo4j_driver.session() as session:
            result = session.run(q)

        return [r for r in result]
