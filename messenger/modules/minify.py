"""Minify message."""


def query(message):
    """Minify message.

    for knowledge graph:
      * keep only node properties: id, name, type
      * keep only edge properties: id, source_id, target_id, type
    for results:
      * keep only qg_id, kg_id
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
            'qg_id': nb['qg_id'],
            'kg_id': nb['kg_id']
        } for nb in result['node_bindings']]
        result['edge_bindings'] = [{
            'qg_id': eb['qg_id'],
            'kg_id': eb['kg_id']
        } for eb in result['edge_bindings']]

    message['knowledge_graph'] = kgraph
    message['results'] = results
    return message
