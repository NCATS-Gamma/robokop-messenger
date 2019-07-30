"""Test normalize."""
# pylint: disable=redefined-outer-name,no-name-in-module,unused-import
# ^^^ this stuff happens because of the incredible way we do pytest fixtures
from messenger.modules.normalize import query as normalize
from tests.fixtures import nonsense_curie, whatis_doid


def test_normalize_nonsense(nonsense_curie):
    """Test that normalize() returns the input for curies that cannot be normalized."""
    result = normalize(nonsense_curie)
    assert result['query_graph']['nodes'][0]['curie'] == ['NONSENSE']


def test_normalize_ebola(whatis_doid):
    """Test that normalize() maps DOIDs to MONDO ids."""
    result = normalize(whatis_doid)
    assert result['query_graph']['nodes'][0]['curie'] == ['MONDO:0005737']
