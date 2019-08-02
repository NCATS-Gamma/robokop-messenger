"""Reasoner service server."""

import os
import sys
from types import ModuleType
from importlib import import_module
import logging.config
import pkg_resources
from flask import request
import yaml
from jinja2 import Environment, PackageLoader
from flask_cors import CORS
import connexion

# Set up default logger.
with pkg_resources.resource_stream('messenger', 'logging.yml') as f:
    config = yaml.safe_load(f.read())
logging.config.dictConfig(config)
handlers = logging.getLogger('messenger').handlers
fh = next(h for h in handlers if isinstance(h, logging.FileHandler))
logdir = os.path.dirname(fh.baseFilename)
if not os.path.exists(logdir):
    os.makedirs(logdir)

summary = {
    'title': 'ROBOKOP Messenger',
    'version': '1.0.0',
    'description': 'ROBOKOP reasoning services, compliant with NCATS Reasoner Standards',
    'email': 'patrick@covar.com',
    'endpoints': []
}
dirname = os.path.join(os.path.dirname(__file__), 'modules')
operations = [op[:-3] for op in os.listdir(dirname) if op.endswith('.py')]

# create controllers module
controllers = ModuleType('controllers')
for operation in operations:
    md = import_module(f"messenger.modules.{operation}")

    def query(mdi=md):
        """Wrap query method as Flask controller."""
        return mdi.query(request.json['message'], **request.json['options']), 200
    query.__name__ = operation
    summary['endpoints'].append({
        'operation': operation,
        'description': md.query.__doc__
    })

    setattr(controllers, operation, query)
sys.modules['controllers'] = controllers

# build full spec using Jinja
env = Environment(
    loader=PackageLoader('messenger', 'templates')
)
template = env.get_template('reasoner.yaml')
spec_string = template.render(**summary)
with open('openapi.yaml', 'w') as f:
    f.write(spec_string)
spec = yaml.load(spec_string, Loader=yaml.SafeLoader)

# build Flask app
app = connexion.FlaskApp(
    __name__,
    specification_dir='.'
)

# apply spec to app
app.add_api(spec)

# add CORS support
CORS(app.app)
