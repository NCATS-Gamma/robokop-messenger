"""Test screening."""
# pylint: disable=redefined-outer-name,no-name-in-module,unused-import
# ^^^ this stuff happens because of the incredible way we do pytest fixtures
import json
from messenger.modules.score import query as score
from messenger.modules.screen import query as screen
from fixtures import weighted2


def test_screen(weighted2):
    """Test that screen() runs without errors."""
    result = screen(score(weighted2), max_results=3)
    assert len(result['results']) == 3
