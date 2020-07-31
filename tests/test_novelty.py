"""Test novelty weighting."""
# pylint: disable=redefined-outer-name,no-name-in-module,unused-import
# ^^^ this stuff happens because of the incredible way we do pytest fixtures
import json

from reasoner_pydantic import Request

from messenger.modules.weight_novelty import query as novelty
from messenger.modules.weight_correctness import query as correctness
from .fixtures import to_weight


def test_weight(to_weight):
    """Test that weight() runs without errors."""
    request = Request(message=novelty(to_weight))
    result = correctness(request)
