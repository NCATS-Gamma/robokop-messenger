"""Test nab."""
from time import time
from .fixtures import yanked, cop_yanked
from messenger.modules.yank import query as yank


def test_yank(cop_yanked):
    start = time()
    yank(cop_yanked)
    print(f'{time() - start} seconds elapsed.')
