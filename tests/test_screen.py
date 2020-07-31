"""Test screening."""
# pylint: disable=redefined-outer-name,no-name-in-module,unused-import
# ^^^ this stuff happens because of the incredible way we do pytest fixtures
import json

from reasoner_pydantic import Request

from messenger.modules.score import query as score
from messenger.modules.screen import query as screen
from .fixtures import weighted2


def test_screen(weighted2):
    """Test that screen() runs without errors."""
    request = Request(message=score(weighted2).dict())
    result = screen(request, max_results=3).dict()
    assert len(result['results']) == 3
