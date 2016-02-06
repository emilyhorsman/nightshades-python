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

    attrs = {
        'expiry_threshold_seconds': nightshades.api.expiry_interval_seconds
    }

    if 'completed' in unit:
        attrs['completed'] = unit.get('completed')

    if 'description' in unit:
        attrs['description'] = unit.get('description')

    if 'start_time' in unit:
        attrs['start_time'] = unit.get('start_time').isoformat()

    if 'expiry_time' in unit:
        attrs['expiry_time'] = unit.get('expiry_time').isoformat()

    if 'tags' in unit:
        attrs['tags'] = unit.get('tags')

    if attrs:
        data['attributes'] = attrs

    return data


@api.route('/me')
@logged_in
def me():
    user = nightshades.api.get_user(g.user_id)
    return jsonify({
        'data': {
            'type': 'user',
            'attributes': {
                'name': user.get('name')
            }
        }
    })


@api.route('/units', methods=['DELETE'])
@logged_in
def delete_unit():
    nightshades.api.cancel_ongoing_unit(g.user_id)
    return jsonify({ 'status': 'success' })


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


@api.route('/units', methods=['POST'])
@logged_in
@validate_payload(type='unit', attributes_required=True)
def create_unit():
    payload     = request.get_json()['data']
    attributes  = payload['attributes']
    seconds     = attributes.get('delta', 1500)
    description = attributes.get('description', None)
    result      = nightshades.api.start_unit(g.user_id, seconds, description)

    tags = attributes.get('tags', None)
    if tags:
        valid_tags = nightshades.api.set_tags(result.get('id'), tags)
        result['tags'] = valid_tags

    ret = { 'data': serialize_unit_data(result) }
    return jsonify(ret), 201


@api.route('/units/<uuid>')
@logged_in
@validate_uuid
def show_unit(uuid):
    unit = nightshades.api.get_unit(uuid, user_id = g.user_id)

    ret  = { 'data': serialize_unit_data(unit) }
    return jsonify(ret), 200


@api.route('/units/<uuid>', methods=['PATCH'])
@logged_in
@validate_uuid
@validate_payload(type = 'unit', attributes_required = True)
def update_unit(uuid):
    attributes = request.get_json()['data']['attributes']

    tags = attributes.get('tags', False)
    if tags:
        valid_tags = nightshades.api.set_tags(uuid, tags, user_id = g.user_id)
        return jsonify({
            'data': serialize_unit_data({
                'id': uuid,
                'tags': valid_tags
            })
        })

    if attributes.get('completed', False):
        res = nightshades.api.mark_complete(uuid, user_id = g.user_id)
        if not res:
            raise errors.InvalidAPIUsage('Unit is not yet complete or has already been marked complete')

        return jsonify({
            'data': serialize_unit_data({
                'id': uuid,
                'completed': True
            })
        })

    raise errors.InvalidAPIUsage('No operations to perform')
