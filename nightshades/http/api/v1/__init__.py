import peewee
from flask import Blueprint, jsonify, current_app

api = Blueprint('api.v1', __name__, url_prefix='/v1')

import nightshades
from nightshades.models import db
from . import authentication
from . import endpoints
from . import errors


@api.after_request
def apply_cors(response):
    cors = current_app.config.get('CORS', False)
    if cors:
        response.headers['Access-Control-Allow-Origin'] = current_app.config.get('CORS')
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PATCH, DELETE'
        response.headers['Access-Control-Allow-Headers'] = 'content-type'

    return response


@api.errorhandler(peewee.DoesNotExist)
def handle_not_found(e):
    return errors.json_error(404, 'Not Found'), 404


@api.errorhandler(nightshades.api.HasOngoingUnitAlready)
def handle_has_ongoing_unit(e):
    return errors.json_error(400, 'Unit already ongoing'), 400


@api.errorhandler(nightshades.api.UsageError)
def handle_invalid_api_usage(e):
    return errors.InvalidAPIUsage.to_dict(e), getattr(e, 'status_code', 400)
