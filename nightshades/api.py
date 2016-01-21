from .query_helpers import form_select, form_insert, form_delete, form_update

# This is how long one has after the expiry_time to mark a unit as complete.
expiry_interval = "INTERVAL '5 minutes'"

class Unit:
    def __init__(self, conn, user_id, unit_id):
        self.conn = conn
        self.user_id  = user_id
        self.unit_id  = unit_id
        self.sql_opts = {
            'id': self.unit_id,
            'user_id': self.user_id
        }

    # Returns the time delta between the expiry time and now. Can be used to
    # check the time left of a unit, or how long ago a unit was complete.
    def time_left(self):
        sql = form_select(
            select = ('expiry_time - NOW()', 'nightshades.units'),
            where  = ('user_id=%(user_id)s', 'id=%(id)s'),)

        with self.conn.cursor() as curs:
            curs.execute(sql, self.sql_opts)
            res = curs.fetchone()
            return res[0]

    def mark_complete(self):
        sql = form_update(
            update = ('nightshades.units', 'completed=TRUE'),
            where  = ('user_id=%(user_id)s',
                      'id=%(id)s',
                      'completed=FALSE',
                      'NOW() >= expiry_time',
                      'NOW() <= expiry_time + {}'.format(expiry_interval),))

        with self.conn.cursor() as curs:
            curs.execute(sql, self.sql_opts)
            res = curs.rowcount
            if res == 1:
                self.conn.commit()
                return (True,)

            # Something fishy has happened.
            self.conn.rollback()
            return (False, 'Tried to mark {} units complete.'.format(res))

class User:
    def __init__(self, conn, user_id):
        self.conn = conn
        self.user_id = user_id
        self.sql_opts = {
            'user_id': self.user_id
        }

    def get_units(self, show_incomplete=False):
        completion = []
        if not show_incomplete:
            completion.append("completed='t'")

        sql = form_select(
            select = ('id, completed, start_time, expiry_time', 'nightshades.units'),
            where  = ['user_id=%(user_id)s'] + completion,
            order  = 'expiry_time DESC',)

        with self.conn.cursor() as curs:
            curs.execute(sql, self.sql_opts)
            return curs.fetchall()

    # Returns True if a unit is currently in progress. There is a particular
    # threshold for when a unit is considered expired. The unit must be marked
    # complete within this threshold.
    def is_unit_ongoing(self):
        sql = form_select(
            select = ('COUNT(id)', 'nightshades.units'),
            where  = ('user_id=%(user_id)s',
                      'completed=FALSE',
                      'expiry_time + {} > NOW()'.format(expiry_interval)),)

        with self.conn.cursor() as curs:
            curs.execute(sql, self.sql_opts)
            res = curs.fetchone()
            return res[0] > 0

    def cancel_ongoing_unit(self):
        sql = form_delete(
            delete = 'nightshades.units',
            where  = ('user_id=%(user_id)s',
                      'completed=FALSE',
                      'expiry_time > NOW()',
                      'expiry_time <= NOW() + {}'.format(expiry_interval),))

        with self.conn.cursor() as curs:
            curs.execute(sql, self.sql_opts)
            res = curs.rowcount
            if res == 1:
                self.conn.commit()
                return (True, None, None,)

            # Something fishy has happened. There should only ever be one
            # ongoing unit. For caution, we'll rollback this statement.
            self.conn.rollback()
            return (False, 'Expected DELETE statement to affect exactly 1 row', res)

    # Returns back a uuid (which basically acts as a nonce) and a time delta.
    # Returns False if a unit is already ongoing.
    def start_unit(self, minutes=25):
        if self.is_unit_ongoing():
            return (False, 'This user already has an ongoing unit.',)

        sql = form_insert(
            insert    = 'nightshades.units (user_id, start_time, expiry_time)',
            values    = "%(user_id)s, NOW(), NOW() + INTERVAL '%(minutes)s minutes'",
            returning = 'id, expiry_time - NOW()',)

        opts = self.sql_opts.copy()
        opts['minutes'] = minutes

        with self.conn.cursor() as curs:
            curs.execute(sql, opts)
            row = curs.fetchone()
            self.conn.commit()

            return row
