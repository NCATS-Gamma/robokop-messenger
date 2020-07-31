"""ROBOKOP messenger server."""
from functools import wraps
from importlib import import_module
import logging
import logging.config
import os
import pkg_resources

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from reasoner_pydantic import Message
import yaml

# Set up default logger.
with pkg_resources.resource_stream('messenger', 'logging.yml') as f:
    config = yaml.safe_load(f.read())
logdir = 'logs'
if not os.path.exists(logdir):
    os.makedirs(logdir)
config['handlers']['file']['filename'] = os.path.join(logdir, 'messenger.log')
logging.config.dictConfig(config)

LOGGER = logging.getLogger(__name__)

APP = FastAPI(
    title='ROBOKOP Messenger',
    version='1.1.0',
)
APP.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

dirname = os.path.join(os.path.dirname(__file__), 'modules')
operations = [
    op[:-3]
    for op in os.listdir(dirname)
    if op.endswith('.py') and not op.startswith('_')
]

for operation in operations:
    md = import_module(f"messenger.modules.{operation}")
    APP.post('/' + operation, response_model=Message)(md.query)
