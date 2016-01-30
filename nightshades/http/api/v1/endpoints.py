import datetime

from . import api
from . import errors
from .decorators import logged_in, validate_uuid, validate_payload

import nightshades
from flask import request, jsonify, url_for, g


def serialize_unit_data(unit):
    if type(unit) is not dict:
        unit = { 'id': unit }

    data = {
        'type': 'unit',
        'id': unit.get('id'),
        'links': {
            'self': url_for('.show_unit', uuid=unit.get('id'))
        }
    }

    attrs = {}
    if 'completed' in unit:
        attrs['completed'] = unit.get('completed'),

    if 'start_time' in unit:
        attrs['start_time'] = unit.get('start_time').isoformat()

    if 'expiry_time' in unit:
        attrs['expiry_time'] = unit.get('expiry_time').isoformat()

    if attrs:
        data['attributes'] = attrs

    return data


# Get the current users units
@api.route('/units')
@logged_in
def index_units():
    now = datetime.datetime.now()
    beginning_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_today = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    units = nightshades.api.get_units(g.user_id, beginning_of_today, end_of_today)

    ret = {}
    ret['links'] = { 'self': url_for('.index_units') }
    ret['data']  = list(map(serialize_unit_data, units))
    return jsonify(ret)


# Create a new unit and return the UUID and time delta
@api.route('/units', methods=['POST'])
@logged_in
@validate_payload(type='unit')
def create_unit():
    payload = request.get_json()['data']
    seconds = payload.get('attributes', {}).get('delta', 1500)
    try:
        result = nightshades.api.start_unit(g.user_id, seconds)
    except nightshades.api.UsageError as e:
        raise e

    ret = { 'data': serialize_unit_data(result) }
    return jsonify(ret), 201


# Get time delta
@api.route('/units/<uuid>')
@logged_in
@validate_uuid
def show_unit(uuid):
    unit = nightshades.api.get_unit(g.user_id, uuid)
    ret  = { 'data': serialize_unit_data(unit) }
    return jsonify(ret), 200


@api.route('/units/<uuid>', methods=['PATCH'])
@logged_in
@validate_uuid
@validate_payload('unit')
def update_unit(uuid):
    payload = request.get_json()['data']
    if payload.get('attributes', {}).get('completed', False):
        try:
            res = nightshades.api.mark_complete(uuid)
        except nightshades.api.UsageError as e:
            raise e

        if not res:
            raise errors.InvalidAPIUsage('Already marked completed')

        ret = {
            'data': serialize_unit_data({
                'id': uuid,
                'completed': True
            })
        }

        return jsonify(ret), 200

    raise errors.InvalidAPIUsage('No operations to perform')
