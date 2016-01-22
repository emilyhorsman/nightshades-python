from uuid import UUID
from functools import wraps

from flask import abort, request

def validate_uuid(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        try:
            UUID(kwargs['uuid'], version=4)
        except ValueError:
            abort(404)

        return f(*args, **kwargs)

    return wrapped
