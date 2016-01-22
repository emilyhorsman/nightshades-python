from . import api
from .decorators import validate_uuid

from flask import session

# Get the current users units
@api.route('/units')
def index_units():
    return 'GET'

# Create a new unit and return the UUID and time delta
@api.route('/units', methods=['POST'])
def create_unit():
    return 'POST'

# Get time delta
@api.route('/units/<uuid>')
@validate_uuid
def show_unit(uuid):
    return 'GET'

# Mark as complete
@api.route('/units/<uuid>', methods=['PUT'])
@validate_uuid
def update_unit(uuid):
    return 'PUT'
