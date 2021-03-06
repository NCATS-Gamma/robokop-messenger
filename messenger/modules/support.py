"""Literature co-occurrence support."""
from collections import defaultdict
from itertools import combinations
import logging
import os
from uuid import uuid4

import asyncio
from reasoner_pydantic import Request, Message

from messenger.shared.cache import Cache
from messenger.shared.omnicorp import OmnicorpSupport
from messenger.shared.util import batches

logger = logging.getLogger(__name__)

CACHE_HOST = os.environ.get('CACHE_HOST', 'localhost')
CACHE_PORT = os.environ.get('CACHE_PORT', '6379')
CACHE_DB = os.environ.get('CACHE_DB', '0')
CACHE_PASSWORD = os.environ.get('CACHE_PASSWORD', '')


async def count_node_pmids(supporter, node, key, value, cache):
    """Count node PMIDs and add as node property."""
    if value is not None:
        logger.debug(f'{key} is cached')
        support_dict = value
    else:
        logger.debug(f'Computing {key}...')
        support_dict = await supporter.node_pmid_count(node['id'])
        if cache and support_dict['omnicorp_article_count']:
            cache.set(key, support_dict)
    # add omnicorp_article_count to nodes in networkx graph
    node.update(support_dict)


async def count_shared_pmids(
        supporter, support_idx, pair, key, value,
        cache, cached_prefixes, kgraph, pair_to_answer,
        answers,
):
    """Count PMIDS shared by a pair of nodes and create a new support edge."""
    support_edge = value

    if support_edge is None:
        # There are two reasons that we don't get anything back:
        # 1. We haven't evaluated that pair
        # 2. We evaluated, and found it to be zero, and it was part
        #    of a prefix pair that we evaluated all of.  In that case
        #    we can infer that getting nothing back means an empty list
        #    check cached_prefixes for this...
        prefixes = tuple(ident.split(':')[0].upper() for ident in pair)
        if cached_prefixes and prefixes in cached_prefixes:
            logger.debug(f'{pair} should be cached: assume 0')
            support_edge = []
        else:
            logger.debug(f'Computing {pair}...')
            support_edge = await supporter.term_to_term_pmid_count(pair[0], pair[1])
            if cache and support_edge:
                cache.set(key, support_edge)
    else:
        logger.debug(f'{pair} is cached')
    if not support_edge:
        return
    uid = str(uuid4())
    kgraph['edges'].append({
        'type': 'literature_co-occurrence',
        'id': uid,
        'num_publications': support_edge,
        'publications': [],
        'source_database': 'omnicorp',
        'source_id': pair[0],
        'target_id': pair[1],
        'edge_source': 'omnicorp.term_to_term'
    })

    for sg in pair_to_answer[pair]:
        answers[sg]['edge_bindings'].append({
            'qg_id': f's{support_idx}',
            'kg_id': uid
        })


async def query(request: Request) -> Message:
    """Add support to message.

    Add support edges to knowledge_graph and bindings to results.
    """
    message = request.message.dict()

    kgraph = message['knowledge_graph']
    qgraph = message['query_graph']
    answers = message['results']

    # get cache if possible
    try:
        cache = Cache(
            redis_host=CACHE_HOST,
            redis_port=CACHE_PORT,
            redis_db=CACHE_DB,
            redis_password=CACHE_PASSWORD,
        )
    except Exception as err:
        logger.exception(err)
        cache = None

    redis_batch_size = 100

    async with OmnicorpSupport() as supporter:
        # get all node supports

        keys = [f"{supporter.__class__.__name__}({node['id']})" for node in kgraph['nodes']]
        values = []
        for batch in batches(keys, redis_batch_size):
            values.extend(cache.mget(*batch))

        jobs = [
            count_node_pmids(supporter, node, key, value, cache)
            for node, value, key in zip(kgraph['nodes'], values, keys)
        ]

        # Generate a set of pairs of node curies
        pair_to_answer = defaultdict(set)  # a map of node pairs to answers
        for ans_idx, answer_map in enumerate(answers):

            # Get all nodes that are not part of sets and densely connect them
            nodes = sorted([nb['kg_id'] for nb in answer_map['node_bindings'] if isinstance(nb['kg_id'], str)])
            for node_pair in combinations(nodes, 2):
                pair_to_answer[node_pair].add(ans_idx)

            # For all nodes that are within sets, connect them to all nodes that are not in sets
            set_nodes_list_list = [nb['kg_id'] for nb in answer_map['node_bindings'] if isinstance(nb['kg_id'], list)]
            set_nodes = [n for el in set_nodes_list_list for n in el]
            for set_node in set_nodes:
                for node in nodes:
                    node_pair = tuple(sorted((node, set_node)))
                    pair_to_answer[node_pair].add(ans_idx)

        # get all pair supports
        cached_prefixes = cache.get('OmnicorpPrefixes') if cache else None

        keys = [f"{supporter.__class__.__name__}_count({pair[0]},{pair[1]})" for pair in pair_to_answer]
        values = []
        for batch in batches(keys, redis_batch_size):
            values.extend(cache.mget(*batch))

        jobs.extend([
            count_shared_pmids(
                supporter, support_idx, pair, key, value,
                cache, cached_prefixes, kgraph, pair_to_answer,
                answers,
            )
            for support_idx, (pair, value, key) in enumerate(zip(pair_to_answer, values, keys))
        ])
        await asyncio.gather(*jobs)

    message['knowledge_graph'] = kgraph
    message['results'] = answers
    return Message(**message)
