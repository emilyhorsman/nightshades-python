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

    app.run(host = '0.0.0.0')
