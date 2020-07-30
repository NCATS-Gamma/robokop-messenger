"""Test Support."""
from messenger.modules.support import query as support
from fixtures import yanked


def test_support(yanked):
    """Test support()."""
    result = support(yanked).dict()
    assert any(edge['type'] == 'literature_co-occurrence' for edge in result['knowledge_graph']['edges'])
