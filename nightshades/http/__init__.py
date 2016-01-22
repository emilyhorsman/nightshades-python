import os

from .api.v1 import api

from flask import Flask, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get('NIGHTSHADES_APP_SECRET')
app.debug      = os.environ.get('ENVIRONMENT') == 'development'

app.register_blueprint(api)

from . import errorhandlers
