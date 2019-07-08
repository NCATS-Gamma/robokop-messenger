"""Novelty."""
import os
import json
from collections import defaultdict
from messenger.modules.answer import NodeReference, EdgeReference, RemoteKGraph


def query(message):
    """Compute informativeness weights for edges."""
    qgraph = message['query_graph']
    kgraph = message['knowledge_graph']
    results = message['results']

    knodes = kgraph['nodes']
    kedges = kgraph['edges']
    qnodes = qgraph['nodes']
    qedges = qgraph['edges']

    knode_map = {node['id']: node for node in knodes}
    qnode_map = {node['id']: node for node in qnodes}

    score_ids = defaultdict(list)
    for edge in qedges:
        score_ids[edge['source_id']].append((f"{edge['id']}_source", edge, edge['target_id']))
        score_ids[edge['target_id']].append((f"{edge['id']}_target", edge, edge['source_id']))

    for result in results:
        eb_map = {eb['qid']: eb for eb in result['edge_bindings']}
        counters = []
        keys = []
        for nb in result['node_bindings']:
            qnode_id = nb['qid']
            knode_id = nb['kid']
            knode = knode_map[knode_id]
            anchor_node_reference = NodeReference({
                'id': 'n',
                'curie': knode['id'],
                'type': knode['type'][0]
            })
            counts = score_ids[qnode_id]
            base = f"MATCH ({anchor_node_reference}) USING INDEX n:{knode['type'][0]}(id)"
            cypher_counts = []
            for count in counts:
                count_id, edge, end_id = count
                edge_reference = EdgeReference(edge, anonymous=True)
                anon_node_reference = NodeReference(qnode_map[end_id], anonymous=True)
                if edge['target_id'] == qnode_id:
                    source_reference = anon_node_reference
                    target_reference = anchor_node_reference
                elif edge['source_id'] == qnode_id:
                    source_reference = anchor_node_reference
                    target_reference = anon_node_reference
                cypher_counts.append(f"size(({source_reference}){edge_reference}({target_reference})) AS {count_id}")
            counters.append(base + ' WITH ' + ', '.join(cypher_counts + keys))
            keys += [count[0] for count in counts]

        cypher = ' '.join(counters) + ' RETURN ' + ', '.join(keys)

        remote = {
            "url": f"bolt://{os.environ['NEO4J_HOST']}:7687",
            "credentials": {
                "username": "neo4j",
                "password": os.environ['NEO4J_PASSWORD']
            }
        }
        with RemoteKGraph(remote) as driver:
            with driver.session() as session:
                response = session.run(cypher)

        degrees = list(response)[0].data()

        # initialize weights, where they do not exist
        for eb in result['edge_bindings']:
            eb['weight'] = eb.get('weight', 1.0)

        for key in degrees:
            qedge_id = '_'.join(key.split('_')[:-1])
            eb_map[qedge_id]['weight'] /= degrees[key]

    message['results'] = results
    return message

if __name__ == "__main__":
    with open('tests/data/inform.json') as f:
        message = json.load(f)
    message = query(message)
    print(json.dumps(message, indent=2))
