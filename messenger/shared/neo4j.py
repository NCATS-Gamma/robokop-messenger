"""Neo4j lookup utilities."""
from copy import deepcopy
from neo4j import GraphDatabase, basic_auth
from messenger.cypher_adapter import Node, Edge, Graph
from messenger.shared.util import batches, flatten_semilist


def clear(driver):
    """Clear nodes and edges from Neo4j."""
    with driver.session() as session:
        session.run(f"MATCH (n) DETACH DELETE n")


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
    driver = GraphDatabase.driver(
        options['url'],
        auth=basic_auth(options['credentials']['username'], options['credentials']['password'])
    )

    def get_nodes_from_query(query, n):
        with driver.session() as session:
            result = session.run(query_string)

        nodes = [record['n'] for record in result]

        if len(nodes) != n:
            node_ids = [node['id'] for node in nodes]
            raise RuntimeError(f'Went looking for {len(batch)} nodes but only found {len(nodes)}; could not find {set(batch) - set(node_ids)}')
        return nodes

    output = []
    n = 10000
    for batch in batches(node_ids, n):
        # node_ids = [node_id.replace('"', '\\"') for node_id in batch]
        node_ids = batch
        where_string = 'n.id IN [' + ', '.join([f'"{node_id}"' for node_id in node_ids]) + ']'
        query_string = f'MATCH (n:named_thing) WHERE {where_string} RETURN n{{{prop_string}}}'

        try:
            nodes = get_nodes_from_query(query_string, len(batch))
        except RuntimeError:
            # try without using the index on named_thing
            query_string = f'MATCH (n) WHERE {where_string} RETURN n{{{prop_string}}}'
            nodes = get_nodes_from_query(query_string, len(batch))

        for node in nodes:
            if 'type' in node and 'named_thing' in node['type']:
                node['type'].remove('named_thing')
        output += nodes

    return output


def get_edge_properties(edge_ids, **options):
    """Get properties associated with edges."""
    fields = options.pop('fields', None)
    node_ids = options.pop('node_ids', None)
    functions = {
        'source_id': 'startNode(e).id',
        'target_id': 'endNode(e).id',
        'type': 'type(e)'
    }

    if fields is not None:
        prop_string = ', '.join([f'{key}:{functions[key]}' if key in functions else f'{key}:e.{key}' for key in fields])
    else:
        prop_string = ', '.join([f'{key}:{functions[key]}' for key in functions] + ['.*'])

    # get Neo4j connection
    driver = GraphDatabase.driver(
        options['url'],
        auth=basic_auth(options['credentials']['username'], options['credentials']['password'])
    )

    # print(len(edge_ids))

    # batching has never been shown to be helpful except for fulltext indexing
    if False:
    # if node_ids is not None:
        node_id_string = 'n.id IN [' + ', '.join([f'"{node_id}"' for node_id in node_ids]) + ']'
        where_string = 'e.id IN [' + ', '.join([f'"{edge_id}"' for edge_id in edge_ids]) + ']'
        query_string = f'MATCH (n:named_thing)-[e]->() WHERE ({node_id_string}) AND ({where_string}) RETURN e{{{prop_string}}}'

        with driver.session() as session:
            result = session.run(query_string)
        output = [record['e'] for record in result]
    else:
        output = []
        statement = f"CALL db.index.fulltext.queryRelationships('edge_id_index', {{edge_ids}}) YIELD relationship WITH relationship as e RETURN e{{{prop_string}}}"
        with driver.session() as session:
            tx = session.begin_transaction()
            for batch in batches(edge_ids, 1024):
                result = tx.run(statement, {'edge_ids': ' '.join(batch)})

                edges = [record['e'] for record in result]
                if len(edges) != len(batch):
                    edge_ids = [edge['id'] for edge in edges]
                    raise RuntimeError(f'Went looking for {len(batch)} edges but only found {len(edge_ids)}; could not find {set(batch) - set(edge_ids)}')
                output += edges
            tx.commit()

    return output


def edges_from_answers(message, **kwargs):
    """Get edges from answers."""
    edge_ids = [eb['kg_id'] for answer in message['results'] for eb in answer['edge_bindings']]
    edge_ids = flatten_semilist(edge_ids)
    edge_ids = list(set(edge_ids))

    node_ids = [nb['kg_id'] for answer in message['results'] for nb in answer['node_bindings']]
    node_ids = flatten_semilist(node_ids)
    node_ids = list(set(node_ids))
    kwargs['node_ids'] = node_ids

    return get_edge_properties(edge_ids, **kwargs)


def nodes_from_answers(message, **kwargs):
    """Get nodes from answers."""
    node_ids = [nb['kg_id'] for answer in message['results'] for nb in answer['node_bindings']]
    node_ids = flatten_semilist(node_ids)
    node_ids = list(set(node_ids))
    return get_node_properties(node_ids, **kwargs)
