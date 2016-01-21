def form_select(*args, **kwargs):
    symbols = ['SELECT', kwargs['select'][0], 'FROM', kwargs['select'][1]]

    if 'where' in kwargs:
        symbols += ['WHERE', ' AND '.join(kwargs['where'])]

    if 'order' in kwargs:
        symbols += ['ORDER BY', kwargs['order']]

    return ' '.join(symbols) + ';'

def form_insert(*args, **kwargs):
    symbols  = ['INSERT INTO', kwargs['insert']]
    symbols += ['VALUES (', kwargs['values'], ')']

    if 'returning' in kwargs:
        symbols += ['RETURNING', kwargs['returning']]

    return ' '.join(symbols) + ';'

def form_delete(*args, **kwargs):
    symbols = ['DELETE FROM', kwargs['delete']]

    if 'where' in kwargs:
        symbols += ['WHERE', ' AND '.join(kwargs['where'])]

    return ' '.join(symbols) + ';'

def form_update(*args, **kwargs):
    symbols = ['UPDATE', kwargs['update'][0], 'SET', kwargs['update'][1]]

    if 'where' in kwargs:
        symbols += ['WHERE', ' AND '.join(kwargs['where'])]

    return ' '.join(symbols) + ';'

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
                      'NOW() >= expiry_time',))

        with self.conn.cursor() as curs:
            curs.execute(sql, self.sql_opts)
            res = curs.rowcount
            if res == 1:
                self.conn.commit()
                return True

            # Something fishy has happened.
            self.conn.rollback()
            return (False, 'Tried to mark {} units complete.'.format(res))

class User:
    def __init__(self, conn, user_id):
        self.conn = conn
        self.user_id = user_id

    def get_units(self, show_incomplete=False):
        completion = []
        if not show_incomplete:
            completion.append("completed='t'")

        sql = form_select(
            select = ('id, completed, start_time, expiry_time', 'nightshades.units'),
            where  = ['user_id=%(user_id)s'] + completion,
            order  = 'expiry_time DESC',)

        opts = {
            'user_id': self.user_id
        }

        with self.conn.cursor() as curs:
            curs.execute(sql, opts)
            return curs.fetchall()

    # Returns True if a unit is currently in progress.
    def is_unit_ongoing(self):
        sql = form_select(
            select = ('COUNT(id)', 'nightshades.units'),
            where  = ('user_id=%(user_id)s',
                      'completed=FALSE',
                      'expiry_time > NOW()'),)

        opts = {
            'user_id': self.user_id
        }

        with self.conn.cursor() as curs:
            curs.execute(sql, opts)
            res = curs.fetchone()
            return res[0] > 0

    def cancel_ongoing_unit(self):
        sql = form_delete(
            delete = 'nightshades.units',
            where  = ('user_id=%(user_id)s',
                      'completed=FALSE',
                      'expiry_time > NOW()'),)

        opts = {
            'user_id': self.user_id
        }

        with self.conn.cursor() as curs:
            curs.execute(sql, opts)
            res = curs.rowcount
            if res == 1:
                self.conn.commit()
                return True

            # Something fishy has happened. There should only ever be one
            # ongoing unit. For caution, we'll rollback this statement.
            self.conn.rollback()
            return (False, 'More than one row would have been deleted from this operation.')

    # Returns back a uuid (which basically acts as a nonce) and a time delta.
    # Returns False if a unit is already ongoing.
    def start_unit(self, minutes=25):
        if self.is_unit_ongoing():
            return (False, 'This user already has an ongoing unit.',)

        sql = form_insert(
            insert    = 'nightshades.units (user_id, start_time, expiry_time)',
            values    = "%(user_id)s, NOW(), NOW() + INTERVAL '%(minutes)s minutes'",
            returning = 'id, expiry_time - NOW()',)

        opts = {
            'user_id': self.user_id,
            'minutes': minutes
        }

        with self.conn.cursor() as curs:
            curs.execute(sql, opts)
            row = curs.fetchone()
            self.conn.commit()

            return row
