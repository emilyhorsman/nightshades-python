from flask import Blueprint, jsonify

api = Blueprint('api.v1', __name__, url_prefix='/v1')

from . import authentication
from . import endpoints
from . import errors

@api.errorhandler(errors.InvalidAPIUsage)
def handle_invalid_api_usage(e):
    return jsonify(e.to_dict()), e.status_code
