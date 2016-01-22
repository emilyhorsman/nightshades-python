import unittest

from flask import url_for
from flask.ext.testing import TestCase
import nightshades.http

class TestAPIv1(TestCase):
    def create_app(self):
        app = nightshades.http.app
        app.config['TESTING'] = True
        return app

    def test_index_not_found(self):
        res = self.client.get('/')
        self.assert404(res)
        self.assertEqual(res.mimetype, 'application/json')

    def test_index_units(self):
        res = self.client.get(url_for('api.v1.index_units'))
        self.assert200(res)

    def test_create_unit(self):
        res = self.client.post(url_for('api.v1.create_unit'))
        self.assert200(res)

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
