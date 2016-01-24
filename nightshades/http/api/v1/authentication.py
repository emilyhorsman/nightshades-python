from functools import wraps

import jwt
from flask import abort, request, current_app, jsonify, g

from . import api
from . import errors

def authenticate(user_id):
    payload = dict(user_id=user_id)
    token   = jwt.encode(payload, current_app.secret_key, algorithm = 'HS256')
    data    = { 'access_token': token.decode('utf-8') }
    return jsonify(data), 200

def identity():
    user_id = g.get('user_id', None)
    if user_id is not None:
        return user_id

    auth_header = request.headers.get('Authorization', None)
    if not auth_header:
        raise errors.InvalidAPIUsage('Missing Authorization header')

    symbols = auth_header.split()
    if len(symbols) != 2:
        raise errors.InvalidAPIUsage('Invalid Authorization header')

    if symbols[0] != 'JWT':
        raise errors.InvalidAPIUsage('Unsupported Authorization type')

    try:
        payload = jwt.decode(symbols[1], current_app.secret_key, algorithm = 'HS256')
        g.user_id = payload['user_id']
        return g.user_id
    except:
        raise errors.InvalidAPIUsage('Invalid Authorization token')

@api.route('/auth', methods=['POST'])
def authentication():
    return authenticate(request.get_json()['user_id'])
