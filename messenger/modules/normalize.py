"""Normalize node curies."""

import urllib

import requests


def synonymize(*curies):
    """Return a list of synonymous, preferred curies."""
    response = requests.get(
        'https://nodenormalization-sri.renci.org/get_normalized_nodes?'
        + '&'.join(f'curie={urllib.parse.quote(curie)}' for curie in curies)
    )
    if response.status_code == 404:
        return curies
    results = response.json()
    return [
        results[curie]['id']['identifier']
        if results[curie] else
        curie
        for curie in curies
    ]


def ensure_list(list_or_scalar):
    """Convert the input to a list if it is not."""
    if isinstance(list_or_scalar, list):
        return list_or_scalar
    return [list_or_scalar]


def query(message):
    """Normalize."""
    qgraph = message['query_graph']

    qcuries = {
        curie
        for node in qgraph['nodes']
        if 'curie' in node
        for curie in ensure_list(node['curie'])
    }
    try:
        knode_ids = {node['id'] for node in message['knowledge_graph']['nodes']}
    except KeyError:
        # knowledge graph is absent or malformed
        knode_ids = set()
    curie_map = dict(zip(
        qcuries | knode_ids,
        synonymize(*(qcuries | knode_ids))
    ))
    for node in qgraph['nodes']:
        if isinstance(node['curie'], list):
            node['curie'] = [curie_map[ci] for ci in node['curie']]
            break
        node['curie'] = curie_map[node['curie']]
    if ('knowledge_graph' not in message) or ('nodes' not in message['knowledge_graph']):
        return message
    for node in message['knowledge_graph']['nodes']:
        node['id'] = curie_map[node['id']]
    for edge in message['knowledge_graph']['edges']:
        edge['source_id'] = curie_map[edge['source_id']]
        edge['target_id'] = curie_map[edge['target_id']]
    if 'results' not in message:
        return message
    for result in message['results']:
        for binding in result['node_bindings']:
            binding['kg_id'] = curie_map[binding['kg_id']]

    return message
