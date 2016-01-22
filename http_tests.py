import os
import binascii
import unittest

from flask import url_for
from flask.json import dumps
from flask.ext.testing import TestCase

import nightshades.http
from test_helpers import (
        with_user_in_session
)

class TestAPIv1(TestCase):
    def create_app(self):
        app = nightshades.http.app
        app.config['SECRET_KEY'] = binascii.hexlify(os.urandom(24))
        app.config['TESTING'] = True
        return app

    def test_index_not_found(self):
        res = self.client.get('/')
        self.assert404(res)
        self.assertEqual(res.mimetype, 'application/json')

    def test_index_units(self):
        res = self.client.get(url_for('api.v1.index_units'))
        self.assert200(res)

    @with_user_in_session
    def test_create_unit(self):
        payload = {
            'data': {
                'type': 'unit',
                'attributes': { 'delta': 1200 },
            }
        }
        res = self.client.post(url_for('api.v1.create_unit'),
                data = dumps(payload),
                content_type = 'application/json')
        ret = res.json['data']

        self.assertStatus(res, 201)
        self.assertIn('id', ret)
        self.assertEqual(ret['type'], 'unit')
        self.assertEqual(ret['attributes']['delta'], 1200)

    @with_user_in_session
    def test_error_on_second_ongoing_unit(self):
        payload = { 'data': { 'type': 'unit' } }
        res = self.client.post(url_for('api.v1.create_unit'),
                data = dumps(payload),
                content_type = 'application/json')
        self.assertStatus(res, 201)
        self.assertEqual(res.json['data']['attributes']['delta'], 1500)

        res = self.client.post(url_for('api.v1.create_unit'),
                data = dumps(payload),
                content_type = 'application/json')
        self.assertStatus(res, 400)

    def test_show_unit(self):
        url = url_for('api.v1.show_unit', uuid='16fd2706-8baf-433b-82eb-8c7fada847da')
        res = self.client.get(url)
        self.assert200(res)

    def test_update_unit(self):
        url = url_for('api.v1.update_unit', uuid='16fd2706-8baf-433b-82eb-8c7fada847da')
        res = self.client.put(url)
        self.assert200(res)

    def test_invalid_uuid_fails(self):
        url = url_for('api.v1.show_unit', uuid='16fd2706-8baf-433b-82eb-8c7fada8-7da')
        res = self.client.get(url)
        self.assert404(res)


if __name__ == '__main__':
    unittest.main()
