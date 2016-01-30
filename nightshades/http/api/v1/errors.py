import nightshades


class InvalidAPIUsage(nightshades.api.UsageError):
    def __init__(self, message, status_code = 400):
        self.message = message
        self.status_code = status_code

    def to_dict(self):
        ret = {
            'errors': [{
                'status': getattr(self, 'status_code', 400),
                'title': self.message
            }]
        }

        return ret


class Unauthorized(InvalidAPIUsage):
    def __init__(self, message = 'Must be logged in'):
        InvalidAPIUsage.__init__(self, message, 401)
