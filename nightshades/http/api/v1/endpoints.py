import datetime

from . import api
from . import errors
from .authentication import identity
from .decorators import validate_uuid, validate_payload

import nightshades
from nightshades.http.helpers import conn
from flask import request, jsonify, url_for, abort, g

def serialize_unit_data(unit):
    data = {
        'type': 'unit',
        'id': unit[0],
        'links': {
            'self': url_for('.show_unit', uuid=unit[0])
        }
    }

    if isinstance(unit[1], dict):
        data['attributes'] = unit[1]
    else:
        data['attributes'] = {
            'completed':   unit[1],
            'start_time':  unit[2].isoformat(),
            'expiry_time': unit[3].isoformat()
        }

    return data

# Get the current users units
@api.route('/units')
def index_units():
    user = nightshades.api.User(conn(), identity())

    now = datetime.datetime.now()
    beginning_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_today       = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    units = user.get_units(beginning_of_today, end_of_today)

    ret = {}
    ret['links'] = { 'self': url_for('.index_units') }
    ret['data']  = list(map(serialize_unit_data, units))
    return jsonify(ret), 200

# Create a new unit and return the UUID and time delta
@api.route('/units', methods=['POST'])
@validate_payload(type='unit')
def create_unit():
    user    = nightshades.api.User(conn(), identity())
    payload = request.get_json()['data']
    seconds = payload.get('attributes', {}).get('delta', 1500)
    result  = user.start_unit(seconds)

    if not result[0]:
        raise errors.InvalidAPIUsage(result[1])

    uuid, delta = result
    ret = {}
    ret['data'] = serialize_unit_data(
            (uuid, { 'delta': delta.total_seconds() },)
            )

    return jsonify(ret), 201

# Get time delta
@api.route('/units/<uuid>')
@validate_uuid
def show_unit(uuid):
    unit  = nightshades.api.Unit(conn(), identity(), uuid)
    delta = unit.time_left()
    if not delta:
        abort(404)

    ret = {}
    ret['data'] = serialize_unit_data(
            (uuid, { 'delta': delta.total_seconds() },)
            )

    return jsonify(ret), 200

@api.route('/units/<uuid>', methods=['PATCH'])
@validate_payload('unit')
@validate_uuid
def update_unit(uuid):
    payload = request.get_json()['data']
    if payload.get('attributes', {}).get('completed', False):
        unit = nightshades.api.Unit(conn(), identity(), uuid)
        res = unit.mark_complete()
        if not res[0]:
            raise errors.InvalidAPIUsage('Unit not completed')

        ret = {}
        ret['data'] = serialize_unit_data(
                (uuid, { 'completed': True },)
                )

        return jsonify(ret), 200

    raise errors.InvalidAPIUsage('No operations to perform')
