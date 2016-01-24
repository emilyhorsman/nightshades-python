from uuid import UUID
from functools import wraps

from flask import abort, request, jsonify

from . import errors
import nightshades

def validate_uuid(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        try:
            UUID(kwargs['uuid'], version=4)
        except ValueError:
            abort(404)

        return func(*args, **kwargs)

    return wrapped

def validate_payload(type):
    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            payload = request.get_json()
            if not payload or 'data' not in payload:
                raise errors.InvalidAPIUsage('No data')

            if payload['data'].get('type') != type:
                raise errors.InvalidAPIUsage('Wrong type, expected {}'.format(type))

            return func(*args, **kwargs)

        return wrapped
    return decorator
