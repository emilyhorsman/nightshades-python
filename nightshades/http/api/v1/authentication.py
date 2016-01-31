import jwt
import socialauth
from flask import (
    request, redirect, make_response,
    current_app, jsonify, g, abort
)

import nightshades
from . import api
from . import errors


def set_jwt_cookie(resp, value, **kwargs):
    resp.set_cookie(
        'jwt',
        value,
        httponly = True,
        domain = current_app.config.get('COOKIE_DOMAIN'),
        **kwargs
    )


def current_user_id():
    user_id = g.get('user_id', None)
    if user_id is not None:
        return user_id

    # Using cookies to store the token for now but this could be an
    # Authorization header in the future (in addition to cookies).
    token = request.cookies.get('jwt', False)

    if not token:
        return False

    try:
        payload = jwt.decode(token, current_app.secret_key, algorithm = 'HS256')
        if 'user_id' not in payload:
            return False

        g.user_id = payload['user_id']
        return g.user_id
    except:
        raise errors.InvalidAPIUsage('Invalid Authorization token')


def login_or_register(provider, res):
    try:
        user_id = nightshades.api.login_via_provider(
            provider,
            res.get('provider_user_id')
        ).get('id')
    except:
        user_id = nightshades.api.register_user(
            res.get('provider_user_name'),
            provider,
            res.get('provider_user_id')
        )

    return jwt.encode(
        { 'user_id': str(user_id) },
        current_app.secret_key,
        algorithm = 'HS256'
    )


def complete_flow(provider, res):
    resp = make_response(jsonify({ 'status': 'success' }))

    cookie = request.cookies.get('jwt', False)
    if cookie:
        user_id = current_user_id()
        if user_id:
            puid = res.get('provider_user_id')
            nightshades.api.add_new_provider(user_id, provider, puid)

            # Set to the same value
            set_jwt_cookie(resp, cookie)
            return resp

    token = login_or_register(provider, res)
    set_jwt_cookie(resp, token)
    return resp


@api.route('/auth/<provider>')
def authenticate(provider):
    res = socialauth.http_get_provider(
        provider,
        request.base_url,
        request.args,
        current_app.secret_key,
        request.cookies.get('jwt')
    )

    if res.get('status') == 302:
        resp  = make_response(redirect(res.get('redirect')))
        token = res.get('set_token_cookie', False)
        if token:
            set_jwt_cookie(resp, token)

        return resp

    if res.get('status') == 200:
        return complete_flow(provider, res)

    abort(400)


@api.route('/logout')
def logout():
    resp = make_response(jsonify({ 'status': 'success' }))
    set_jwt_cookie(resp, '', expires = 0)
    return resp
