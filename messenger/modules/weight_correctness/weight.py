"""Weight edges."""
import math
import json
from collections import defaultdict


def query(message, **options):
    """Weight kgraph edges based on metadata.

      "19 pubs from CTD is a 1, and 2 should at least be 0.5"
        - cbizon
    """
    relevance = options.pop('relevance', 1 / 4000)  # portion of cooccurrence pubs relevant to question

    wt_min = options.pop('wt_min', 0)  # minimum weight (at 0 pubs)
    wt_max = options.pop('wt_max', 1)  # maximum weight (at inf pubs)
    p50 = options.pop('p50', 2)  # pubs at 50% of wt_max

    def sigmoid(x):
        """Scale with partial sigmoid - the right (concave down) half.

        Such that:
           f(0) = wt_min
           f(inf) = wt_max
           f(p50) = 0.5 * wt_max
        """
        a = 2 * (wt_max - wt_min)
        r = 0.5 * wt_max
        c = wt_max - 2 * wt_min
        k = 1 / p50 * (math.log(r + c) - math.log(a - r - c))
        return a / (1 + math.exp(-k * x)) - c

    kgraph = message['knowledge_graph']
    node_pubs = {n['id']: n.get('omnicorp_article_count', None) for n in kgraph['nodes']}
    all_pubs = 27840000

    results = message['results']
    # map kedges to edge_bindings
    krmap = defaultdict(list)
    for result in results:
        for eb in result['edge_bindings']:
            for kid in eb['kid']:
                krmap[kid].append(eb)

    edges = kgraph['edges']
    for edge in edges:
        edge_pubs = edge.get('num_publications', len(edge.get('publications', [])))
        if edge['type'] == 'literature_co-occurrence':
            source_pubs = int(node_pubs[edge['source_id']])
            target_pubs = int(node_pubs[edge['target_id']])

            cov = (edge_pubs / all_pubs) - (source_pubs / all_pubs) * (target_pubs / all_pubs)
            cov = max((cov, 0.0))
            effective_pubs = cov * all_pubs * relevance
        else:
            effective_pubs = edge_pubs + 1  # consider the curation a pub

        for redge in krmap[edge['id']]:
            redge['weight'] = redge.get('weight', 1.0) * sigmoid(effective_pubs)

    message['knowledge_graph'] = kgraph
    return message
