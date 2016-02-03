import os
import nightshades

if __name__ == '__main__':
    nightshades.load_dotenv()

    # Find me in nightshades/http/__init__.py!
    from nightshades.http import app
    cors = os.environ.get('NIGHTSHADES_CORS', False)
    if cors:
        app.config['CORS'] = cors

    domain = os.environ.get('NIGHTSHADES_COOKIE_DOMAIN', False)
    if domain:
        app.config['COOKIE_DOMAIN'] = domain

    app.config['public_origin'] = os.environ.get('NIGHTSHADES_PUBLIC_ORIGIN', None)

    opbeat = dict(
        organization_id = os.environ.get('NIGHTSHADES_OPBEAT_ORGANIZATION_ID'),
        app_id          = os.environ.get('NIGHTSHADES_OPBEAT_APP_ID'),
        secret_token    = os.environ.get('NIGHTSHADES_OPBEAT_SECRET_TOKEN'),
    )

    if opbeat.get('organization_id', False):
        from opbeat.contrib.flask import Opbeat
        opbeat = Opbeat(app, **opbeat)


    app.run(host = '0.0.0.0')
