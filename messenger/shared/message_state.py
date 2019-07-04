"""Message state analysis tools."""
import pkg_resources
import jsonschema
import yaml


def is_valid(message):
    """Check if message conforms to schema."""
    with pkg_resources.resource_stream('messenger', 'templates/components.yaml') as f:
        base = yaml.load(f, Loader=yaml.SafeLoader)
        schema = base['components']['schemas'].pop('Message')
        schema.update(base)
    try:
        jsonschema.validate(message, schema)
        return True
    except jsonschema.ValidationError:
        return False


def is_answered(message):
    """Check whether results exist."""
    return bool(message['results'])


def kgraph_is_weighted(message):
    """Check whether knowledge graph edges have weights.

    Only valid if message has local knowledge graph.
    """
    if not kgraph_is_local(message):
        raise ValueError('Message does not have local knowledge graph.')
    return all('weight' in edge for edge in message['knowledge_graph']['edges'])


def kgraph_is_local(message):
    """Check whether knowledge graph is local."""
    return 'edges' in message['knowledge_graph']


def answers_are_scored(message):
    """Check whether answers have scores.

    Only valid if answers exist.
    """
    if not is_answered(message):
        raise ValueError('Message has no answers.')
    return all('score' in answer for answer in message['results'])
