"""Neo4j utils for test setup."""
from copy import deepcopy

from .cypher_adapter import Node, Edge, Graph
from messenger.shared.neo4j import Neo4jDatabase
from messenger.shared.util import batches


def get_edge_properties(edge_ids, **options):
    """Get properties associated with edges."""
    fields = options.pop('fields', None)
    node_ids = options.pop('node_ids', None)
    functions = {
        'source_id': 'startNode(e).id',
        'target_id': 'endNode(e).id',
        'type': 'type(e)',
    }
    if options.get('relationship_id', 'property') == 'internal':
        functions['id'] = 'toString(id(e))'

    if fields is not None:
        prop_string = ', '.join([f'{key}:{functions[key]}' if key in functions else f'{key}:e.{key}' for key in fields])
    else:
        prop_string = ', '.join([f'{key}:{functions[key]}' for key in functions] + ['.*'])

    # get Neo4j connection
    driver = Neo4jDatabase(
        url=options['url'],
        credentials=options['credentials'],
    )

    # print(len(edge_ids))

    # batching has never been shown to be helpful except for fulltext indexing
    if node_ids:
        node_id_string = 'n.id IN [' + ', '.join([f'"{node_id}"' for node_id in node_ids]) + ']'
        where_string = 'e.id IN [' + ', '.join([f'"{edge_id}"' for edge_id in edge_ids]) + ']'
        query_string = f'MATCH (n:named_thing)-[e]->() WHERE ({node_id_string}) AND ({where_string}) RETURN e{{{prop_string}}}'

        result = driver.run(query_string)
        output = [record['e'] for record in result]
    else:
        output = []
        if options.get('relationship_id', 'property') == 'internal':
            statement = f"""MATCH ()-[e]->() WHERE id(e) in {{edge_ids}} RETURN e{{{{{prop_string}}}}}"""
            cat_fcn = lambda x: [int(edge_id) for edge_id in x]
        else:
            statement = f"CALL db.index.fulltext.queryRelationships('edge_id_index', {{edge_ids}}) YIELD relationship as e RETURN e{{{{{prop_string}}}}}"
            cat_fcn = ' '.join
            for batch in batches(edge_ids, 1024):
                result = driver.run(statement.format(edge_ids=repr(cat_fcn(batch))))

                edges = [record['e'] for record in result]
                if len(edges) != len(batch):
                    edge_ids = [edge['id'] for edge in edges]
                    raise RuntimeError(f'Went looking for {len(batch)} edges but only found {len(edge_ids)}; could not find {set(batch) - set(edge_ids)}')
                output += edges

    return output


def get_node_properties(node_ids, **options):
    """Get properties associated with nodes."""
    fields = options.pop('fields', None)
    functions = {
        'type': 'labels(n)',
    }

    if fields is not None:
        prop_string = ', '.join([f'{key}:{functions[key]}' if key in functions else f'{key}:n.{key}' for key in fields])
    else:
        prop_string = ', '.join([f'{key}:{functions[key]}' for key in functions] + ['.*'])

    # get Neo4j connection
    driver = Neo4jDatabase(
        url=options['url'],
        credentials=options['credentials'],
    )

    def get_nodes_from_query(query_string, node_ids):
        result = driver.run(query_string)

        nodes = [record['n'] for record in result]

        if len(nodes) != len(node_ids):
            partial_node_ids = [node['id'] for node in nodes]
            raise RuntimeError(f'Went looking for {len(node_ids)} nodes but only found {len(partial_node_ids)}; could not find {set(node_ids) - set(partial_node_ids)}')
        return nodes

    output = []
    n = 10000
    for batch in batches(node_ids, n):
        # node_ids = [node_id.replace('"', '\\"') for node_id in batch]
        node_ids = batch
        where_string = 'n.id IN [' + ', '.join([f'"{node_id}"' for node_id in node_ids]) + ']'
        query_string = f'MATCH (n:named_thing) WHERE {where_string} RETURN n{{{prop_string}}}'

        try:
            nodes = get_nodes_from_query(query_string, batch)
        except RuntimeError:
            # try without using the index on named_thing
            query_string = f'MATCH (n) WHERE {where_string} RETURN n{{{prop_string}}}'
            nodes = get_nodes_from_query(query_string, batch)

        for node in nodes:
            if 'type' in node and 'named_thing' in node['type']:
                node['type'].remove('named_thing')
        output += nodes

    return output


def escape_quotes(string):
    """Escape double quotes in string."""
    return string.replace('"', '\\"')


def dump_kg(driver, kgraph, with_props=False):
    """Dump knowledge graph into Neo4j database."""
    neo4j_graph = Graph("kg", driver)
    kgraph = deepcopy(kgraph)
    nodes = {}
    for node in kgraph["nodes"]:
        node_type = node.pop('type')
        if isinstance(node_type, str):
            node_type = [node_type]
        node_type.append('named_thing')
        node_id = escape_quotes(node.pop('id'))
        properties = {
            "id": node_id
        }
        if with_props:
            properties.update(**node)
        nodes[node_id] = Node(
            labels=node_type,
            properties=properties,
        )
    edges = {}
    for edge in kgraph["edges"]:
        edge_id = edge.pop('id')
        source_id = escape_quotes(edge.pop('source_id'))
        target_id = escape_quotes(edge.pop('target_id'))
        edge_type = edge.pop('type')
        if edge_type == 'literature_co-occurrence':
            continue
        properties = {"id": edge_id}
        if with_props:
            properties.update(**edge)
        edges[edge_id] = Edge(
            nodes[source_id],
            edge_type,
            nodes[target_id],
            properties=properties,
        )

    for node in nodes.values():
        neo4j_graph.add_node(node)

    for edge in edges.values():
        neo4j_graph.add_edge(edge)

    neo4j_graph.commit()
    return
