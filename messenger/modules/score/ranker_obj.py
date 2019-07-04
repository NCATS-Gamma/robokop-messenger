"""ROBOKOP ranking."""

from operator import itemgetter
from collections import defaultdict
from itertools import combinations
import numpy as np
from messenger.shared.neo4j import edges_from_answers
from messenger.shared.util import flatten_semilist
from messenger.shared.message_state import kgraph_is_local
from .dijkstra import dijkstra


class Ranker:
    """Ranker."""

    teleport_weight = 0.001  # probability to teleport along graph (make random inference) in hitting time calculation

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

        self.kedge_by_id = {n['id']: n for n in kedges}
        self.qedge_by_id = {n['id']: n for n in qgraph['edges']}
        self.kedges_by_knodes = defaultdict(list)
        for e in self.kedge_by_id.values():
            self.kedges_by_knodes[tuple(sorted([e['source_id'], e['target_id']]))].append(e)

        self.terminals = terminal_nodes(qgraph)

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

        laplacian, node_ids = self.graph_laplacian(rgraph)
        terminals = [n for n in node_ids if any([n.startswith(t) for t in self.terminals])]

        voltages = []
        node_id_set = set(node_ids)
        for from_id, to_id in combinations(terminals, 2):
            node_ids_sorted = [from_id] + list(node_id_set - {from_id, to_id}) + [to_id]
            idx = [node_ids.index(node_id) for node_id in node_ids_sorted]
            idx = np.expand_dims(np.array(idx), axis=1)
            idy = np.transpose(idx)
            L = laplacian[idx, idy]
            voltages.append(1 / voltage_from_laplacian(L))

        score = np.mean(voltages)

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

        # add teleportation to allow leaps of faith
        laplacian = laplacian + self.teleport_weight * (num_nodes * np.eye(num_nodes) - np.ones((num_nodes, num_nodes)))
        return laplacian, node_ids

    def get_rgraph(self, answer):
        """Get "ranker" subgraph."""
        # get list of nodes, and knode_map
        rnodes = []
        knode_map = defaultdict(set)
        for nb in answer['node_bindings']:
            qnode_id = nb['qid']
            knode_ids = nb['kid']
            if not isinstance(knode_ids, list):
                knode_ids = [knode_ids]
            for knode_id in knode_ids:
                rnode_id = f"{qnode_id}/{knode_id}"
                rnodes.append(rnode_id)
                knode_map[knode_id].add(rnode_id)

        # get "result" edges
        redges = []
        for eb in answer['edge_bindings']:
            qedge_id = eb['qid']
            kedge_ids = eb['kid']
            if qedge_id[0] == 's':
                continue
            qedge = self.qedge_by_id[qedge_id]
            if not isinstance(kedge_ids, list):
                kedge_ids = [kedge_ids]
            for kedge_id in kedge_ids:
                kedge = self.kedge_by_id[kedge_id]

                # find source and target
                # qedge direction may not match kedge direction
                # we'll go with the qedge direction
                candidate_source_ids = [f"{qedge['source_id']}/{kedge['source_id']}", f"{qedge['source_id']}/{kedge['target_id']}"]
                candidate_target_ids = [f"{qedge['target_id']}/{kedge['source_id']}", f"{qedge['target_id']}/{kedge['target_id']}"]
                source_id = next(rnode_id for rnode_id in rnodes if rnode_id in candidate_source_ids)
                target_id = next(rnode_id for rnode_id in rnodes if rnode_id in candidate_target_ids)
                edge = {
                    'weight': kedge['weight'],
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
                for source_id in knode_map[kedge['source_id']]:
                    for target_id in knode_map[kedge['target_id']]:
                        edge = {
                            'weight': kedge['weight'],
                            'source_id': source_id,
                            'target_id': target_id
                        }
                        redges.append(edge)

        return rnodes, redges


def terminal_nodes(question):
    """Return indices of terminal question nodes.

    Terminal nodes are those that either:
    a) have curies
    b) have degree 1
    c) have maximum dijkstra distance from a named node
    """
    nodes = question['nodes']
    simple_edges = [(edge['source_id'], edge['target_id'], 1) for edge in question['edges']]
    is_named = [node['id'] for node in nodes if node.get('curie', False)]
    degree = defaultdict(int)
    for edge in simple_edges:
        degree[edge[0]] += 1
        degree[edge[1]] += 1
    is_terminal = [key for key in degree if degree[key] == 1]
    if len(is_named) >= 2:
        return list(set(is_terminal + is_named))
    distances = dijkstra(simple_edges, is_named)
    is_far_from_named = [key for key in distances if distances[key] == np.max(list(distances.values()))]
    return list(set(is_terminal + is_named + is_far_from_named))


def voltage_from_laplacian(L):
    """Compute voltage drop given Laplacian matrix."""
    iv = np.zeros(L.shape[0])
    iv[0] = -1
    iv[-1] = 1
    results = np.linalg.lstsq(L, iv, rcond=None)
    potentials = results[0]
    return potentials[-1] - potentials[0]
