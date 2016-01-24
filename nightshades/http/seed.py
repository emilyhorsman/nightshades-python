"""
This provides useful seed data meant for development only.
"""

import os

from . import app

import nightshades
from flask import current_app

if bool(os.environ.get('NIGHTSHADES_DEVELOPMENT_SEED')) and app.debug:
    def seed():
        seed_user_sql  = "INSERT INTO nightshades.users (name) VALUES ('Alice') RETURNING id"
        seed_units_sql = """
        INSERT INTO nightshades.units (user_id, completed, start_time, expiry_time)
        VALUES
        (%(user_id)s, FALSE, NOW(), NOW() + INTERVAL '1 hour'),
        (%(user_id)s, TRUE, NOW() - INTERVAL '120 minutes', NOW() - INTERVAL '90 minutes'),
        (%(user_id)s, TRUE, NOW() - INTERVAL '180 minutes', NOW() - INTERVAL '155 minutes')
        """

        with nightshades.connection() as conn:
            with conn.cursor() as curs:
                curs.execute(seed_user_sql)
                conn.commit()

                user_id = curs.fetchone()[0]

                with app.app_context():
                    current_app.seed_user_id = user_id
                    app.logger.debug('User ID set to {} for seed mode.'.format(current_app.seed_user_id))

                curs.execute(seed_units_sql, { 'user_id': user_id })
                conn.commit()
