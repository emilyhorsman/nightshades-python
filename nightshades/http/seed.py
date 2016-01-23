"""
This provides useful seed data meant for development only. It also sets a
user_id in the session before all requests.
"""

import os

from . import app

import nightshades
from flask import session, current_app

if bool(os.environ.get('NIGHTSHADES_DEVELOPMENT_SEED')) and app.debug:
    @app.before_request
    def before_request():
        with app.app_context():
            session['user_id'] = current_app.seed_user_id
            app.logger.debug('User ID set by seed mode: {}'.format(session['user_id']))


    def seed():
        with nightshades.connection() as conn:
            with conn.cursor() as curs:
                curs.execute("INSERT INTO nightshades.users (name) VALUES ('Alice') RETURNING id")
                conn.commit()

                with app.app_context():
                    current_app.seed_user_id = curs.fetchone()[0]
                    app.logger.debug('User ID set to {} for seed mode.'.format(current_app.seed_user_id))
