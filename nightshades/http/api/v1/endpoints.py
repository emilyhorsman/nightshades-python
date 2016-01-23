from . import api
from . import errors
from .decorators import validate_uuid, validate_payload, with_connection

import nightshades

from flask import request, session, jsonify, url_for, abort

# Get the current users units
@api.route('/units')
def index_units():
    return 'GET'

# Create a new unit and return the UUID and time delta
@api.route('/units', methods=['POST'])
@validate_payload(type='unit')
@with_connection
def create_unit(conn):
    user    = nightshades.api.User(conn, session['user_id'])
    payload = request.get_json()['data']
    seconds = payload.get('attributes', {}).get('delta', 1500)
    result  = user.start_unit(seconds)

    if not result[0]:
        raise errors.InvalidAPIUsage(result[1])

    uuid, delta = result
    ret = {}
    ret['data'] = {
        'type': 'unit',
        'id': uuid,
        'attributes': { 'delta': delta.total_seconds() },
        'links': { 'self': url_for('.show_unit', uuid=uuid) }
    }

    return jsonify(ret), 201

# Get time delta
@api.route('/units/<uuid>')
@validate_uuid
@with_connection
def show_unit(conn, uuid):
    unit  = nightshades.api.Unit(conn, session['user_id'], uuid)
    delta = unit.time_left()
    if not delta:
        abort(404)

    ret = {}
    ret['data'] = {
        'type': 'unit',
        'id': uuid,
        'attributes': { 'delta': delta.total_seconds() },
        'links': { 'self': url_for('.show_unit', uuid=uuid) }
    }

    return jsonify(ret), 200

# Mark as complete
@api.route('/units/<uuid>', methods=['PUT'])
@validate_uuid
def update_unit(uuid):
    return 'PUT'
