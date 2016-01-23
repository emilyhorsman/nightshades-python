import os
import binascii
import unittest
import uuid

from flask import url_for
from flask.json import dumps
from flask.ext.testing import TestCase

import nightshades.http
import nightshades.query_helpers
from test_helpers import (
        with_user_in_session, with_connection_and_cursor
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

    def test_show_unit_fails_without_user(self):
        pass

    @with_user_in_session
    def test_show_unit_not_found(self):
        res = self.client.get(url_for('api.v1.show_unit', uuid=uuid.uuid4()))
        self.assertStatus(res, 404)

    @with_user_in_session
    @with_connection_and_cursor
    def test_show_unit(self, conn, curs):
        with self.client.session_transaction() as session:
            user_id = session['user_id']

        sql = nightshades.query_helpers.form_insert(
                insert    = 'nightshades.units (user_id, start_time, expiry_time)',
                values    = "%s, NOW(), NOW() + '1 minute'",
                returning = 'id')
        curs.execute(sql, (session['user_id'],))
        conn.commit()
        uuid = curs.fetchone()[0]

        url = url_for('api.v1.show_unit', uuid=uuid)
        res = self.client.get(url)
        ret = res.json
        self.assert200(res)
        self.assertTrue(ret['data']['attributes']['delta'] >= 59.9)
        self.assertTrue(ret['data']['attributes']['delta'] <= 60)

        sql = nightshades.query_helpers.form_update(
                update = ('nightshades.units', "expiry_time=NOW() - INTERVAL '1 second'"),
                where  = ('user_id=%s', 'id=%s'))
        curs.execute(sql, (session['user_id'], uuid,))
        conn.commit()

        res = self.client.get(url)
        ret = res.json
        self.assert200(res)
        self.assertTrue(ret['data']['attributes']['delta'] < -0.9)
        self.assertTrue(ret['data']['attributes']['delta'] >= -1.1)

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
