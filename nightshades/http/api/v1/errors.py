from flask import jsonify

class InvalidAPIUsage(Exception):
    def __init__(self, message):
        Exception.__init__(self)
        self.message     = message
        self.status_code = 400

    def to_dict(self):
        ret = {
            'errors': [{
                'status': self.status_code,
                'title': self.message
            }]
        }

        return ret
