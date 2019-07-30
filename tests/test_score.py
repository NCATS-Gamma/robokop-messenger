"""Test scoring."""
# pylint: disable=redefined-outer-name,no-name-in-module,unused-import
# ^^^ this stuff happens because of the incredible way we do pytest fixtures
import json
from messenger.modules.score import query as score
from fixtures import weighted2


def test_score(weighted2):
    """Test that score() runs without errors."""
    result = score(weighted2)
