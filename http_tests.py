import os
import unittest
import datetime
from unittest.mock import patch
from uuid import uuid4

import iso8601
import jwt
import flask
from werkzeug.http import parse_cookie
from flask import url_for, g
from flask.json import dumps
from flask.ext.testing import TestCase
from peewee import SQL

import nightshades.http
from nightshades.models import User, LoginProvider, Unit, Tag


def mock_authenticate_start(provider, redirect_url, params, token_secret, token_cookie):
    return {
        'status': 302,
        'redirect': 'https://api.{}.com'.format(provider),
        'set_token_cookie': 'foobar'
    }


def mock_authenticate_finish(provider_user_id):
    def http_get_provider(provider, redirect_url, params, token_secret, token_cookie):
        return {
            'status': 200,
            'provider_user_id': provider_user_id,
            'provider_user_name': 'Alice'
        }

    return http_get_provider


class TestAPIv1(TestCase):
    def create_app(self):
        app = nightshades.http.app
        app.config['SECRET_KEY'] = 'sekret'
        app.config['TESTING'] = True

        return app


class Test404ErrorHandler(TestAPIv1):
    def test_error_handler(self):
        res = self.client.get('/foobar')
        self.assertStatus(res, 404)
        self.assertEqual(res.json['errors'][0]['title'], 'Not Found')


class TestAuthentication(TestAPIv1):
    @patch('socialauth.http_get_provider', mock_authenticate_start)
    def test_authenticate_start(self):
        res = self.client.get(url_for('api.v1.authenticate', provider = 'twitter'))
        self.assertStatus(res, 302)
        self.assertEqual(res.headers.get('Location'), 'https://api.twitter.com')
        self.assertIn('jwt=foobar; HttpOnly;', res.headers.get('Set-Cookie'))

    def test_authenticate_finish_new_user(self):
        puid = str(uuid4())
        f = mock_authenticate_finish(puid)
        with patch('socialauth.http_get_provider', f):
            url = url_for('api.v1.authenticate', provider = 'twitter')
            res = self.client.get(url)
            self.assertStatus(res, 200)

        cookies = parse_cookie(res.headers.get('Set-Cookie'))
        token = jwt.decode(cookies.get('jwt'), 'sekret')

        user = User.get(User.id == token.get('user_id'))
        login = LoginProvider.get(
            LoginProvider.user == user,
            LoginProvider.provider == 'twitter'
        )
        self.assertEqual(user.name, 'Alice')
        self.assertEqual(login.provider_user_id, puid)

    def test_authenticate_login_existing_user(self):
        user  = User.create(name = 'Alice')
        login = LoginProvider.create(
            user             = user,
            provider         = 'twitter',
            provider_user_id = str(uuid4())
        )

        f = mock_authenticate_finish(login.provider_user_id)
        with patch('socialauth.http_get_provider', f):
            url = url_for('api.v1.authenticate', provider = 'twitter')
            res = self.client.get(url)
            self.assertStatus(res, 200)

        cookies = parse_cookie(res.headers.get('Set-Cookie'))
        token   = jwt.decode(cookies.get('jwt'), 'sekret')

        logged_in_user = User.get(User.id == token.get('user_id'))
        self.assertEqual(logged_in_user.id, user.id)

    def test_authenticate_add_new_login_provider(self):
        # Set up an existing user and login provider record.
        user = User.create(name = 'Alice')
        login = LoginProvider.create(
            user             = user,
            provider         = 'twitter',
            provider_user_id = str(uuid4())
        )

        # Log the user in.
        token = jwt.encode({ 'user_id': str(user.id) }, 'sekret')
        self.client.set_cookie('localhost', 'jwt', token)

        puid = str(uuid4())
        f = mock_authenticate_finish(puid)
        with patch('socialauth.http_get_provider', f):
            url = url_for('api.v1.authenticate', provider = 'facebook')
            res = self.client.get(url)

            self.assertStatus(res, 200)

        cookies = parse_cookie(res.headers.get('Set-Cookie'))
        self.assertEqual(cookies.get('jwt'), token.decode('utf-8'),
            msg='The token should not have changed since the user is already logged in')

        # Ensure the user now has two valid login providers
        self.assertEqual(LoginProvider.select().where(
            LoginProvider.user == user.id
        ).count(), 2)

        self.assertTrue(LoginProvider.get(
            LoginProvider.user == user.id,
            LoginProvider.provider == 'facebook',
            LoginProvider.provider_user_id == puid
        ))


class TestUnauthorized(TestAPIv1):
    def test_index_units_is_protected(self):
        res = self.client.get(url_for('api.v1.index_units'))
        self.assertStatus(res, 401)

    def test_create_unit_is_protected(self):
        res = self.client.post(url_for('api.v1.create_unit'))
        self.assertStatus(res, 401)

    def test_show_unit_is_protected(self):
        res = self.client.get(url_for('api.v1.show_unit', uuid = uuid4()))
        self.assertStatus(res, 401)

    def test_update_unit_is_protected(self):
        res = self.client.patch(url_for('api.v1.update_unit', uuid = uuid4()))
        self.assertStatus(res, 401)


class TestEndpoints(TestAPIv1):
    def setUp(self):
        self.user = User.create(name = 'Alice')
        token = jwt.encode({ 'user_id': str(self.user.id) }, 'sekret')
        self.client.set_cookie('localhost', 'jwt', token)


class TestIndexUnits(TestEndpoints):
    def test_index_units(self):
        a = Unit.create(user = self.user)
        b = Unit.create(
            user        = self.user,
            completed   = True,
            start_time  = SQL("NOW() - INTERVAL '30 minutes'"),
            expiry_time = SQL("NOW() - INTERVAL '5 minutes'")
        )

        res = self.client.get(url_for('api.v1.index_units'))
        self.assertStatus(res, 200)

        ret = res.json['data']
        self.assertEqual(ret[0]['id'], str(a.id))
        self.assertEqual(ret[1]['id'], str(b.id))


class TestCreateUnit(TestEndpoints):
    def test_create_unit(self):
        payload = {
            'data': {
                'type': 'unit',
                'attributes': { 'delta': 1200 }
            }
        }
        res = self.client.post(
            url_for('api.v1.create_unit'),
            data = dumps(payload),
            content_type = 'application/json'
        )
        ret = res.json['data']

        self.assertStatus(res, 201)
        self.assertEqual(ret['type'], 'unit')
        self.assertIn('id', ret)

    def test_error_on_second_ongoing_unit(self):
        Unit.create(user = self.user)
        payload = { 'data': { 'type': 'unit' } }
        res = self.client.post(
            url_for('api.v1.create_unit'),
            data = dumps(payload),
            content_type = 'application/json'
        )
        self.assertStatus(res, 400)


class TestShowUnit(TestEndpoints):
    def test_show_unit(self):
        unit = Unit.create(user = self.user)
        res  = self.client.get(url_for('api.v1.show_unit', uuid = unit.id))
        self.assertStatus(res, 200)

        ret   = res.json['data']
        attrs = ret['attributes']

        self.assertIn('completed', attrs)

        # Ensure dates are provided in ISO 8601 format
        # YYYY-MM-DDTHH:MM:SS.mmmmmm+HH:MM
        try:
            iso8601.parse_date(attrs['start_time'])
            iso8601.parse_date(attrs['expiry_time'])
        except iso8601.ParseError as e:
            self.fail(e)


class TestUpdateUnit(TestEndpoints):
    def test_update_unit(self):
        unit = Unit.create(
            user        = self.user,
            completed   = False,
            start_time  = SQL("NOW() - INTERVAL '5 minutes'"),
            expiry_time = SQL("NOW() - INTERVAL '1 second'")
        )

        payload = {}
        payload['data'] = {
            'type': 'unit',
            'id': unit.id,
            'attributes': { 'completed': True }
        }
        res = self.client.patch(
            url_for('api.v1.update_unit', uuid = unit.id),
            data = dumps(payload),
            content_type = 'application/json'
        )
        self.assertStatus(res, 200)

    def test_already_marked_complete(self):
        unit = Unit.create(user = self.user, completed = True)

        payload = {}
        payload['data'] = {
            'type': 'unit',
            'id': unit.id,
            'attributes': { 'completed': True }
        }
        res = self.client.patch(
            url_for('api.v1.update_unit', uuid = unit.id),
            data = dumps(payload),
            content_type = 'application/json'
        )
        self.assertStatus(res, 400)

    def test_no_operations(self):
        unit = Unit.create(user = self.user)
        payload = {}
        payload['data'] = { 'type': 'unit', 'id': unit.id }
        res = self.client.patch(
            url_for('api.v1.update_unit', uuid = unit.id),
            data = dumps(payload),
            content_type = 'application/json'
        )
        self.assertStatus(res, 400)


class TestValidateUUID(TestEndpoints):
    def test_invalid_uuid(self):
        res = self.client.patch(url_for('api.v1.update_unit', uuid = 'abcd'))
        self.assertStatus(res, 404)


class TestValidatePayload(TestEndpoints):
    def test_no_data(self):
        res = self.client.patch(
            url_for('api.v1.update_unit', uuid = str(uuid4())),
            data = '{}',
            content_type = 'application/json'
        )
        self.assertStatus(res, 400)
        self.assertEqual(res.json['errors'][0]['title'], 'No data')

    def test_wrong_type(self):
        res = self.client.patch(
            url_for('api.v1.update_unit', uuid = str(uuid4())),
            data = '{"data":{"type":"foobar"}}',
            content_type = 'application/json'
        )
        self.assertStatus(res, 400)
        self.assertIn('type', res.json['errors'][0]['title'])


if __name__ == '__main__':
    unittest.main()
