from functools import wraps

import jwt
from flask import abort, request, current_app, jsonify

from . import api
from . import errors

def authenticate(user_id):
    payload = dict(user_id=user_id)
    token   = jwt.encode(payload, current_app.secret_key, algorithm = 'HS256')
    data    = { 'access_token': token.decode('utf-8') }
    return jsonify(data), 200

def identity():
    auth_header = request.headers.get('Authorization', None)
    if not auth_header:
        raise errors.InvalidAPIUsage('Missing Authorization header')

    symbols = auth_header.split()
    if len(symbols) != 2:
        raise errors.InvalidAPIUsage('Invalid Authorization header')

    if symbols[0] != 'JWT':
        raise errors.InvalidAPIUsage('Unsupported Authorization type')

    payload = jwt.decode(symbols[1], current_app.secret_key, algorithm = 'HS256')
    return payload['user_id']

def require_user(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        return func(identity, *args, **kwargs)

    return wrapped

@api.route('/auth', methods=['POST'])
def authentication():
    return authenticate(request.get_json()['user_id'])
