"""Normalize node curies."""

import requests


def synonymize(curie, node_type):
    response = requests.post(f"http://robokop.renci.org:6010/api/synonymize/{curie}/{node_type}/")
    if response.status_code != 200:
        return curie
    return response.json()['id']


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

    return message
