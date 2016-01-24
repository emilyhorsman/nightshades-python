import os

from .api.v1 import api
from . import helpers

from flask import Flask, g

app = Flask(__name__)
app.secret_key = os.environ.get('NIGHTSHADES_APP_SECRET')
app.debug      = os.environ.get('ENVIRONMENT') == 'development'

app.register_blueprint(api)


@app.teardown_appcontext
def close_connection(exception):
    conn = g.get('conn', None)
    if conn is not None:
        conn.close()

from . import errorhandlers

if bool(os.environ.get('NIGHTSHADES_DEVELOPMENT_SEED')) and app.debug:
    from . import seed  # pragma: no cover
    seed.seed()  # pragma: no cover
