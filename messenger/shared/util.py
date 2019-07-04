"""Reasoner filters utilities."""
import random
import string


def random_string(length=10):
    """Return a random N-character-long string."""
    return ''.join(random.choice(string.ascii_lowercase) for x in range(length))


def argsort(x, reverse=False):
    """Return the indices that would sort the array."""
    return [p[0] for p in sorted(enumerate(x), key=lambda elem: elem[1], reverse=reverse)]


def flatten_semilist(x):
    """Convert a semi-nested list - a list of (lists and scalars) - to a flat list."""
    # convert to a list of lists
    lists = [n if isinstance(n, list) else [n] for n in x]
    # flatten nested list
    return [e for el in lists for e in el]


def batches(arr, n):
    """Iterate over arr by batches of size n."""
    for i in range(0, len(arr), n):
        yield arr[i:i + n]


class Text:
    """Utilities for processing text."""

    @staticmethod
    def get_curie(text):
        return text.upper().split(':')[0] if ':' in text else None

    @staticmethod
    def un_curie(text):
        return text.split(':')[1] if ':' in text else text

    @staticmethod
    def short(obj, limit=80):
        text = str(obj) if obj else None
        return (text[:min(len(text), limit)] + ('...' if len(text) > limit else '')) if text else None

    @staticmethod
    def path_last(text):
        return text.split('/')[-1:][0] if '/' in text else text

    @staticmethod
    def obo_to_curie(text):
        return ':'.join(text.split('/')[-1].split('_'))

    @staticmethod
    def snakify(text):
        decomma = '_'.join(text.split(','))
        dedash = '_'.join(decomma.split('-'))
        resu = '_'.join(dedash.split())
        return resu
