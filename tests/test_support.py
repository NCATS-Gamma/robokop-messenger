"""Test Support."""
import pytest

from messenger.modules.support import query as support
from .fixtures import yanked


@pytest.mark.asyncio
async def test_support(yanked):
    """Test support()."""
    result = (await support(yanked)).dict()
    assert any(
        edge['type'] == 'literature_co-occurrence'
        for edge in result['knowledge_graph']['edges']
    )
