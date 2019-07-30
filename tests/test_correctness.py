"""Test correctness (publication) weighting."""
# pylint: disable=redefined-outer-name,no-name-in-module,unused-import
# ^^^ this stuff happens because of the incredible way we do pytest fixtures
import json
from messenger.modules.weight_correctness import query as weight
from tests.fixtures import to_weight


def test_weight(to_weight):
    """Test that weight() runs without errors."""
    result = weight(to_weight)
    print(json.dumps(result, indent=4))
