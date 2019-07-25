"""Novelty."""
import uuid
from collections import defaultdict
from messenger.modules.answer import NodeReference, EdgeReference, KGraph


def get_rgraph(result, message):
    """Get "ranker" subgraph."""
    qedges_by_id = {
        qedge['id']: qedge
        for qedge in message['query_graph']['edges']
    }
    kedges_by_id = {
        kedge['id']: kedge
        for kedge in message['knowledge_graph']['edges']
    }

    rnodes = result['node_bindings']

    # get "result" edges
    redges = []
    for eb in result['edge_bindings']:
        qedge_id = eb['qg_id']
        kedge_id = eb['kg_id']
        if qedge_id.startswith('s'):
            continue

        qedge = qedges_by_id[qedge_id]
        kedge = kedges_by_id[kedge_id]

        # find source and target
        # qedge direction may not match kedge direction
        # we'll go with the qedge direction
        kg_source_id = next(
            rnode['kg_id']
            for rnode in rnodes
            if (
                rnode['qg_id'] == qedge['source_id'] and
                (
                    kedge['source_id'] == rnode['kg_id'] or
                    kedge['target_id'] == rnode['kg_id']
                )
            )
        )
        kg_target_id = next(
            rnode['kg_id']
            for rnode in rnodes
            if (
                rnode['qg_id'] == qedge['target_id'] and
                (
                    kedge['source_id'] == rnode['kg_id'] or
                    kedge['target_id'] == rnode['kg_id']
                )
            )
        )
        edge = {
            'id': str(uuid.uuid4()),
            'eb': eb,
            'qg_source_id': qedge['source_id'],
            'qg_target_id': qedge['target_id'],
            'kg_source_id': kg_source_id,
            'kg_target_id': kg_target_id,
        }
        redges.append(edge)

    return {
        'nodes': rnodes,
        'edges': redges
    }


def query(message):
    """Compute informativeness weights for edges."""
    qgraph = message['query_graph']
    kgraph = message['knowledge_graph']
    results = message['results']

    knodes = kgraph['nodes']
    kedges = kgraph['edges']
    qnodes = qgraph['nodes']
    qedges = qgraph['edges']

    knode_map = {knode['id']: knode for knode in knodes}
    qnode_map = {qnode['id']: qnode for qnode in qnodes}
    qedge_map = {qedge['id']: qedge for qedge in qedges}

    for result in results:
        rgraph = get_rgraph(result, message)
        redges_by_id = {
            redge['id']: redge
            for redge in rgraph['edges']
        }

        count_plans = defaultdict(lambda: defaultdict(list))
        for redge in rgraph['edges']:
            count_plans[redge['kg_source_id']][(redge['eb']['qg_id'], redge['qg_target_id'])].append(
                redge['id']
            )
            count_plans[redge['kg_target_id']][(redge['eb']['qg_id'], redge['qg_source_id'])].append(
                redge['id']
            )

        counters = []
        keys = []
        count_to_redge = {}
        for idx, (ksource_id, plan) in enumerate(count_plans.items()):
            knode = knode_map[ksource_id]
            anchor_node_reference = NodeReference({
                'id': 'n',
                'curie': knode['id'],
                'type': knode['type']
            })
            base = f"MATCH ({anchor_node_reference})"
            # base += f"USING INDEX n:{knode['type'][0]}(id)"
            cypher_counts = []
            new_keys = []
            for jdx, (qlink, redge_ids) in enumerate(plan.items()):
                qedge_id, qtarget_id = qlink
                count_id = f"c{idx:03d}{chr(97 + jdx)}"
                qedge = qedge_map[qedge_id]
                edge_reference = EdgeReference(qedge, anonymous=True)
                anon_node_reference = NodeReference(qnode_map[qtarget_id], anonymous=True)
                if qedge['target_id'] == qtarget_id:
                    source_reference = anon_node_reference
                    target_reference = anchor_node_reference
                elif qedge['source_id'] == qtarget_id:
                    source_reference = anchor_node_reference
                    target_reference = anon_node_reference
                cypher_counts.append(f"size(({source_reference}){edge_reference}({target_reference})) AS {count_id}")
                new_keys.append(count_id)
                count_to_redge[count_id] = redge_ids
            counters.append(base + ' WITH ' + ', '.join(cypher_counts + keys))
            keys += new_keys

        cypher = ' '.join(counters) + ' RETURN ' + ', '.join(keys)

        with KGraph(message) as driver:
            with driver.session() as session:
                response = session.run(cypher)

        degrees = list(response)[0].data()

        for key in degrees:
            for redge_id in count_to_redge[key]:
                eb = redges_by_id[redge_id]['eb']
                eb['weight'] = eb.get('weight', 1.0) / degrees[key]

    message['results'] = results
    return message
