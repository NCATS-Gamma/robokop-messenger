"""Test ranking of big sets."""
# pylint: disable=redefined-outer-name,no-name-in-module,unused-import
# ^^^ this stuff happens because of the incredible way we do pytest fixtures
import json

from reasoner_pydantic import Request

from messenger.modules.answer import query as answer
from messenger.modules.weight_correctness import query as correctness
from messenger.modules.weight_novelty import query as novelty
from messenger.modules.score import query as score
from .fixtures import bigset


def test_answer_bigset(bigset):
    """Test that answer() handles empty queries."""
    request = Request(message=answer(bigset).dict())
    request = Request(message=novelty(request).dict())
    result = score(request)


def test_score_leafset(bigset):
    """Test that answer() handles empty queries."""
    bigset.message.query_graph.nodes = bigset.message.query_graph.nodes[:3]
    bigset.message.query_graph.edges = bigset.message.query_graph.edges[:2]
    request = Request(message=answer(bigset).dict())
    request = Request(message=correctness(request).dict())
    result = score(request)
