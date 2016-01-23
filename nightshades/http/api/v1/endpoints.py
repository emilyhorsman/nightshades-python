import datetime

from . import api
from . import errors
from .decorators import validate_uuid, validate_payload, with_connection

import nightshades
from flask import request, session, jsonify, url_for, abort

def serialize_unit(unit):
    return {
        'type': 'unit',
        'id': unit[0],
        'attributes': {
            'completed':   unit[1],
            'start_time':  unit[2],
            'expiry_time': unit[3]
        }
    }

# Get the current users units
@api.route('/units')
@with_connection
def index_units(conn):
    user  = nightshades.api.User(conn, session['user_id'])

    now = datetime.datetime.now()
    beginning_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_today       = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    units = user.get_units(beginning_of_today, end_of_today)

    ret = {}
    ret['data'] = list(map(serialize_unit, units))
    return jsonify(ret), 200

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

@api.route('/units/<uuid>', methods=['PATCH'])
@validate_payload('unit')
@validate_uuid
@with_connection
def update_unit(conn, uuid):
    payload = request.get_json()['data']
    if payload.get('attributes', {}).get('completed', False):
        unit = nightshades.api.Unit(conn, session['user_id'], uuid)
        res = unit.mark_complete()
        if not res[0]:
            raise errors.InvalidAPIUsage('Unit not completed')

        ret = {}
        ret['data'] = {
            'type': 'unit',
            'id': uuid,
            'attributes': { 'completed': True },
            'links': { 'self': url_for('.show_unit', uuid=uuid) }
        }

        return jsonify(ret), 200

    raise errors.InvalidAPIUsage('No operations to perform')
