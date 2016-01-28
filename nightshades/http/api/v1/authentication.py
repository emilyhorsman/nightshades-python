from urllib.parse import parse_qsl

import jwt
import oauth2
from flask import request, current_app, jsonify, g, make_response, abort

import nightshades
from nightshades.http.helpers import conn

from . import api
from . import errors

provider_api_url = {
    'twitter': 'https://api.twitter.com{}'
}

def authenticate(user_id):
    payload = dict(user_id=user_id)
    token   = jwt.encode(payload, current_app.secret_key, algorithm = 'HS256')
    data    = { 'access_token': token.decode('utf-8') }
    return jsonify(data), 200


def token_from_authorization_header(header):
    if not header:
        raise errors.InvalidAPIUsage('Missing Authorization header')

    symbols = header.split()
    if len(symbols) != 2:
        raise errors.InvalidAPIUsage('Invalid Authorization header')

    if symbols[0] != 'JWT':
        raise errors.InvalidAPIUsage('Unsupported Authorization type')

    return symbols[1]


def identity():
    user_id = g.get('user_id', None)
    if user_id is not None:
        return user_id

    token = token_from_authorization_header(request.headers.get('Authorization'))

    try:
        payload = jwt.decode(token, current_app.secret_key, algorithm = 'HS256')
        g.user_id = payload['user_id']
        return g.user_id
    except:
        raise errors.InvalidAPIUsage('Invalid Authorization token')


def get_consumer(provider):
    if provider not in ('twitter',):
        abort(400)

    return oauth2.Consumer(
        key    = os.environ.get('NIGHTSHADES_{}_CONSUMER_KEY'.format(provider)),
        secret = os.environ.get('NIGHTSHADES_{}_SECRET_KEY'.format(provider)))


@api.route('/auth/<provider>', methods=['POST'])
def start_provider_flow(provider):
    client = oauth2.Client(get_consumer(provider))

    url = provider_api_url[provider].format('/oauth/request_token')
    resp, content = client.request(url, 'GET')
    if resp.status != 200:
        abort(500)

    oauth_values       = dict(parse_qsl(content.decode('utf-8')))
    oauth_token        = oauth_values.get('oauth_token', False)
    oauth_token_secret = oauth_values.get('oauth_token_secret', False)
    if not oauth_token or not oauth_token_secret:
        abort(400)

    url = provider_api_url[provider].format('/oauth/authenticate?oauth_token={}')
    url = url.format(oauth_token)

    resp = make_response(jsonify({ 'redirect': url }))

    payload = {}
    payload[provider] = { 'oauth_token_secret': oauth_token_secret }
    token   = jwt.encode(payload, current_app.secret_key, algorithm = 'HS256')
    resp.set_cookie('jwt', token, httponly=True)

    return resp


@api.route('/auth/<provider>', methods=['GET'])
def complete_provider_flow(provider):
    oauth_verifier = request.args.get('oauth_verifier')
    oauth_token    = request.args.get('oauth_token')
    if not oauth_verifier or not oauth_token:
        abort(400)

    consumer = get_consumer(provider)

    payload = request.cookies.get('jwt')
    try:
        payload = jwt.decode(payload, current_app.secret_key)
        oauth_token_secret = payload[provider]['oauth_token_secret']
    except:
        abort(400)

    token = oauth2.Token(oauth_token, oauth_token_secret)
    token.set_verified(oauth_verifier)

    url    = provider_api_url[provider].format('/oauth/access_token')
    client = oauth2.Client(consumer, token)
    resp, content = client.request(url, 'POST')
    if resp.status != 200:
        abort(400)

    provider_user        = dict(parse_qsl(content.decode('utf-8')))
    provider_user_id     = provider_user.get('user_id', False)
    provider_screen_name = provider_user.get('screen_name', None)
    if not provider_user_id:
        abort(400)

    opts = {}
    if provider_screen_name is not None:
        opts['name'] = provider_screen_name

    user = nightshades.api.UserAuthentication(conn(), provider, provider_user_id, opts)
    if not user.user_id:
        abort(401)

    payload = { 'user_id': user.user_id }
    token   = jwt.encode(payload, current_app.secret_key)
    resp.set_cookie('jwt', token)

    return resp
