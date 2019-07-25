"""ROBOKOP ranking."""

from operator import itemgetter
from collections import defaultdict
from itertools import combinations, product
import re
import numpy as np
from messenger.shared.neo4j import edges_from_answers
from messenger.shared.util import flatten_semilist
from messenger.shared.message_state import kgraph_is_local


class Ranker:
    """Ranker."""

    def __init__(self, message):
        """Create ranker."""
        kgraph = message['knowledge_graph']
        qgraph = message['query_graph']

        if kgraph_is_local(message):
            kedges = kgraph['edges']
        else:
            kedges = edges_from_answers(message)
        if not any('weight' in kedge for kedge in kedges):
            for kedge in kedges:
                kedge['weight'] = 1

        self.qnode_by_id = {n['id']: n for n in qgraph['nodes']}
        self.kedge_by_id = {n['id']: n for n in kedges}
        self.qedge_by_id = {n['id']: n for n in qgraph['edges']}
        self.kedges_by_knodes = defaultdict(list)
        for e in kedges:
            self.kedges_by_knodes[tuple(sorted([e['source_id'], e['target_id']]))].append(e)

    def rank(self, answers):
        """Generate a sorted list and scores for a set of subgraphs."""
        # get subgraph statistics
        answers = [self.score(answer) for answer in answers]

        answers.sort(key=itemgetter('score'), reverse=True)
        return answers

    def score(self, answer):
        """Compute answer score."""
        # answer is a list of dicts with fields 'id' and 'bound'
        rgraph = self.get_rgraph(answer)

        laplacian = self.graph_laplacian(rgraph)
        nonset_node_ids = [idx for idx, node_id in enumerate(rgraph[0]) if not node_id.startswith('_')]

        score = 1 / kirchhoff(laplacian, nonset_node_ids)

        # fail safe to nuke nans
        score = score if np.isfinite(score) and score >= 0 else -1
        answer['score'] = score
        return answer

    def graph_laplacian(self, rgraph):
        """Generate graph Laplacian."""
        node_ids, edges = rgraph

        # compute graph laplacian for this case with potentially duplicated nodes
        num_nodes = len(node_ids)
        laplacian = np.zeros((num_nodes, num_nodes))
        index = {node_id: node_ids.index(node_id) for node_id in node_ids}
        for edge in edges:
            source_id, target_id, weight = edge['source_id'], edge['target_id'], edge['weight']
            i, j = index[source_id], index[target_id]
            laplacian[i, j] += -weight
            laplacian[j, i] += -weight
            laplacian[i, i] += weight
            laplacian[j, j] += weight

        return laplacian

    def get_rgraph(self, answer):
        """Get "ranker" subgraph."""
        # TODO: for each set node with degree 1, add a new neighbor

        # get list of nodes, and knode_map
        rnodes = []
        knode_map = defaultdict(set)
        for nb in answer['node_bindings']:
            qnode_id = nb['qg_id']
            knode_id = nb['kg_id']
            rnode_id = f"{qnode_id}/{knode_id}"
            if self.qnode_by_id[qnode_id].get('set', False):
                rnode_id = '_' + rnode_id
            rnodes.append(rnode_id)
            knode_map[knode_id].add(rnode_id)

        # get "result" edges
        redges = []
        for eb in answer['edge_bindings']:
            qedge_id = eb['qg_id']
            kedge_id = eb['kg_id']
            if qedge_id[0] == 's':
                continue
            qedge = self.qedge_by_id[qedge_id]
            kedge = self.kedge_by_id[kedge_id]

            # find source and target
            # qedge direction may not match kedge direction
            # we'll go with the qedge direction
            source_id = first_match(f"_?{qedge['source_id']}/({kedge['source_id']}|{kedge['target_id']})", rnodes)
            target_id = first_match(f"_?{qedge['target_id']}/({kedge['source_id']}|{kedge['target_id']})", rnodes)
            edge = {
                'weight': eb['weight'],
                'source_id': source_id,
                'target_id': target_id
            }
            redges.append(edge)

        # get "support" edges
        # We cannot get these the same way as the result edges
        # because they do not appear in the qgraph.
        for nodes in combinations(sorted(knode_map.keys()), 2):
            # loop over edges connecting these nodes
            for kedge in self.kedges_by_knodes[nodes]:
                if kedge['type'] != 'literature_co-occurrence':
                    continue
                # loop over rnodes connected by this edge
                for source_id, target_id in product(knode_map[kedge['source_id']], knode_map[kedge['target_id']]):
                    edge = {
                        'weight': kedge['weight'],
                        'source_id': source_id,
                        'target_id': target_id
                    }
                    redges.append(edge)

        return rnodes, redges


def kirchhoff(L, keep):
    """Compute Kirchhoff index, including only specific nodes."""
    num_nodes = L.shape[0]
    cols = []
    for x, y in combinations(keep, 2):
        d = np.zeros(num_nodes)
        d[x] = -1
        d[y] = 1
        cols.append(d)
    x = np.stack(cols, axis=1)

    return np.trace(x.T @ np.linalg.lstsq(L, x, rcond=None)[0])


def first_match(pattern, strings):
    """Return the first string in the list matching the regular expression."""
    return next(
        string
        for string in strings
        if re.fullmatch(pattern, string) is not None
    )
