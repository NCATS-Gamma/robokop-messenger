"""Rank."""
from messenger.shared.util import flatten_semilist
from messenger.shared.neo4j import edges_from_answers
from messenger.shared.message_state import kgraph_is_local
from .ranker_obj import Ranker


def query(message):
    """Score answers.

    This is mostly glue around the heavy lifting in ranker_obj.Ranker
    """
    kgraph = message['knowledge_graph']
    answers = message['results']

    # resistance distance ranking
    pr = Ranker(message)
    answers = pr.rank(answers)

    # finish
    message['results'] = answers
    return message
