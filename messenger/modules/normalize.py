"""Normalize node curies."""
import urllib

import os
import httpx
from reasoner_pydantic import Request, Message

# Makes NN url configurable

NN_URL = os.environ.get("NN_URL", "https://nodenormalization-sri.renci.org/get_normalized_nodes?")



def synonymize(*curies):
    """Return a list of synonymous, preferred curies."""
    response = httpx.get(
        NN_URL + '&'.join(f'curie={urllib.parse.quote(curie)}' for curie in curies)
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


async def query(request: Request) -> Message:
    """Normalize."""
    message = request.message.dict()
    qgraph = message['query_graph']

    qcuries = {
        curie
        for node in qgraph['nodes']
        if 'curie' in node
        for curie in ensure_list(node['curie'])
    }
    try:
        knode_ids = {node['id'] for node in message['knowledge_graph']['nodes']}
    except (KeyError, TypeError):
        # knowledge graph is absent or malformed
        knode_ids = set()
    curies = {
        curie
        for curie in qcuries | knode_ids
        if curie
    }
    curie_map = dict(zip(
        curies,
        synonymize(*(curies))
    ))
    for node in qgraph['nodes']:
        if not node.get('curie', None):
            continue
        node['curie'] = [curie_map[ci] for ci in ensure_list(node['curie'])]
    if not message.get('knowledge_graph', None) or ('nodes' not in message['knowledge_graph']):
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

    return Message(**message)
