import nightshades
from flask import jsonify


def json_error(status, title):
    ret = {
        'errors': [{
            'status': status,
            'title': title
        }]
    }

    return jsonify(ret)



class InvalidAPIUsage(nightshades.api.UsageError):
    def __init__(self, message, status_code = 400):
        self.message = message
        self.status_code = status_code

    def to_dict(self):
        return json_error(self.status_code, self.message)


class Unauthorized(InvalidAPIUsage):
    def __init__(self, message = 'Must be logged in'):
        InvalidAPIUsage.__init__(self, message, 401)
