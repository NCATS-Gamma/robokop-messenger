"""Normalize node curies."""

import os
import requests


def synonymize(curie, node_type):
    response = requests.post(f"http://{os.environ['BUILDER_HOST']}:{os.environ['BUILDER_PORT']}/api/synonymize/{curie}/{node_type}/")
    if response.status_code != 200:
        return curie
    return response.json()['id']


def typelist2str(node_types):
    """Convert possible list of types to single string."""
    if isinstance(node_types, str):
        return node_types
    if isinstance(node_types, list):
        return next(
            node_type
            for node_type in node_types
            if node_type not in ('named_thing', 'Base')
        )
    else:
        raise ValueError(f'Unsupport node-type type {type(node_types)}')


def query(message):
    """Normalize."""
    qgraph = message['query_graph']

    for node in qgraph['nodes']:
        if not ('curie' in node and 'type' in node):
            continue
        # synonymize/normalize curie
        curies = node['curie']
        if isinstance(curies, list):
            pass
        elif isinstance(curies, str):
            curies = [curies]
        else:
            raise ValueError(f'Curie should be a list or str, but it is a {type(curies)}.')
        curies = [synonymize(curie, node['type']) for curie in curies]
        node['curie'] = curies
    if ('knowledge_graph' not in message) or ('nodes' not in message['knowledge_graph']):
        return message
    curie_map = {
        node['id']: synonymize(node['id'], typelist2str(node['type']))
        for node in message['knowledge_graph']['nodes']
    }
    for node in message['knowledge_graph']['nodes']:
        node['id'] = curie_map[node['id']]
    for edge in message['knowledge_graph']['edges']:
        edge['source_id'] = curie_map[edge['source_id']]
        edge['target_id'] = curie_map[edge['target_id']]
    if 'results' not in message:
        return message
    for result in message['results']:
        for nb in result['node_bindings']:
            nb['kg_id'] = curie_map[nb['kg_id']]

    return message
