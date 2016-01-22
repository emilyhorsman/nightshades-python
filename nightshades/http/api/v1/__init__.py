from flask import Blueprint

api = Blueprint('api.v1', __name__, url_prefix='/v1')

from . import endpoints
