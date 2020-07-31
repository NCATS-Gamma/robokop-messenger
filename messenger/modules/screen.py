"""Filter by score."""
import heapq
import json
import logging
import operator

from reasoner_pydantic import Request, Message

from messenger.shared.util import flatten_semilist

logger = logging.getLogger(__name__)


def query(request: Request, *, max_results: int = 3) -> Message:
    """Prescreen subgraphs.

    Keep the top max_results, by their total edge weight.
    """
    message = request.message.dict()
    if max_results < 0:
        return message

    kgraph = message['knowledge_graph']
    answers = message['results']

    prescreen_scores = [answer['score'] for answer in answers]

    prescreen_sorting = [x[0] for x in heapq.nlargest(max_results, enumerate(prescreen_scores), key=operator.itemgetter(1))]

    answers = [answers[i] for i in prescreen_sorting]

    node_ids = set()
    edge_ids = set()
    for answer in answers:
        these_node_ids = [nb['kg_id'] for nb in answer['node_bindings']]
        these_node_ids = flatten_semilist(these_node_ids)
        node_ids.update(these_node_ids)

        these_edge_ids = [eb['kg_id'] for eb in answer['edge_bindings']]
        these_edge_ids = flatten_semilist(these_edge_ids)
        edge_ids.update(these_edge_ids)

    if 'edges' in kgraph:
        kgraph['edges'] = [e for e in kgraph['edges'] if e['id'] in edge_ids]
        kgraph['nodes'] = [n for n in kgraph['nodes'] if n['id'] in node_ids]
        message['knowledge_graph'] = kgraph

    message['results'] = answers
    return Message(**message)
