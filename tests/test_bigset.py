"""Test ranking of big sets."""
# pylint: disable=redefined-outer-name,no-name-in-module,unused-import
# ^^^ this stuff happens because of the incredible way we do pytest fixtures
import json
from messenger.modules.answer import query as answer
from messenger.modules.yank import query as yank
from messenger.modules.weight_correctness import query as correctness
from messenger.modules.weight_novelty import query as novelty
from messenger.modules.score import query as score
from fixtures import bigset


def test_answer_bigset(bigset):
    """Test that answer() handles empty queries."""
    result = score(novelty(yank(answer(bigset))))


def test_score_leafset(bigset):
    """Test that answer() handles empty queries."""
    bigset['query_graph']['nodes'] = bigset['query_graph']['nodes'][:3]
    bigset['query_graph']['edges'] = bigset['query_graph']['edges'][:2]
    result = score(correctness(yank(answer(bigset))))
