import os

from .api.v1 import api
from nightshades.models import db

from flask import Flask

app = Flask(__name__)
app.secret_key = os.environ.get('NIGHTSHADES_APP_SECRET')
app.debug      = os.environ.get('ENVIRONMENT') == 'development'

app.register_blueprint(api)


@app.teardown_appcontext
def close_connection(exception):
    if not db.is_closed():
        db.close()

from . import errorhandlers
