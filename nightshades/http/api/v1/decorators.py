from uuid import UUID
from functools import wraps

from flask import abort, request

from .authentication import current_user_id
from . import errors


def logged_in(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        try:
            if not current_user_id():
                raise
        except:
            raise errors.Unauthorized

        return func(*args, **kwargs)

    return wrapped


def validate_uuid(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        try:
            UUID(kwargs['uuid'], version=4)
        except ValueError:
            abort(404)

        return func(*args, **kwargs)

    return wrapped


def validate_payload(type, attributes_required = False):
    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            payload = request.get_json()
            if not payload or 'data' not in payload:
                raise errors.InvalidAPIUsage('No data')

            if payload['data'].get('type') != type:
                raise errors.InvalidAPIUsage('Wrong type, expected {}'.format(type))

            if attributes_required and not payload['data'].get('attributes', False):
                raise errors.InvalidAPIUsage('No attributes given')

            return func(*args, **kwargs)

        return wrapped
    return decorator
