"""Minify message."""


def query(message):
    """Minify message.

    for knowledge graph:
      * keep only node properties: id, name, type
      * keep only edge properties: id, source_id, target_id, type
    for results:
      * keep only qid, kid
    """
    kgraph = message['knowledge_graph']
    results = message['results']

    kgraph['nodes'] = [{
        'id': node['id'],
        'name': node['name'],
        'type': node['type']
    } for node in kgraph['nodes']]
    kgraph['edges'] = [{
        'id': edge['id'],
        'source_id': edge['source_id'],
        'target_id': edge['target_id'],
        'type': edge['type']
    } for edge in kgraph['edges']]
    for result in results:
        result['node_bindings'] = [{
            'qid': nb['qid'],
            'kid': nb['kid']
        } for nb in result['node_bindings']]
        result['edge_bindings'] = [{
            'qid': eb['qid'],
            'kid': eb['kid']
        } for eb in result['edge_bindings']]

    message['knowledge_graph'] = kgraph
    message['results'] = results
    return message
