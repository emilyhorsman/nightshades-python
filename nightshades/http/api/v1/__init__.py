import peewee
from flask import Blueprint, jsonify

api = Blueprint('api.v1', __name__, url_prefix='/v1')

import nightshades
from nightshades.models import db
from . import authentication
from . import endpoints
from . import errors


@api.errorhandler(peewee.DoesNotExist)
def handle_not_found(e):
    return jsonify({ 'errors': [
        { 'status': 404, 'title': 'Not Found' }
    ]}), 404


@api.errorhandler(nightshades.api.UsageError)
def handle_invalid_api_usage(e):
    return jsonify(errors.InvalidAPIUsage.to_dict(e)), getattr(e, 'status_code', 400)
