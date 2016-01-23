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

    # Returns a tuple containing,
    # (new tags in database, invalid tags not inserted)
    def update_tags(self, tag_csv):
        if tag_csv.count(',') >= 5:
            return (False, 'A unit can only have 5 tags')

        # Get the old ones out of the way
        remove_sql = form_delete(
                delete = 'nightshades.unit_tags',
                where  = ('unit_id=%(id)s',))


        # ....aaaaand the messy bit to bring in the new ones.
        invalids    = []
        insert_opts = []
        mogrify_me  = []
        for _tag in set(tag_csv.split(',')): # Unique only
            # Skip any blank tags
            tag = _tag.strip()
            if not tag:
                continue

            # Validate the tag, spit back a validation tuple
            if len(tag) > 40:
                invalids.append((tag, 'Over 40 characters',))
                continue

            # We need to insert multiple values,
            # INSERT ... VALUES (id, 'a'), (id, 'b');
            #                   (%s, %s),  (%s, %s);
            #
            # psycopg2 is expecting positional arguments so we need to give
            # it a list of `uid,tag,uid,tag` to mogrify into
            # the list of `(%s, %s)`s.
            mogrify_me.append("(%s,%s)")

            # Flattened list of (uid,tag)
            insert_opts.append(self.unit_id)
            insert_opts.append(tag)

        # This is suckage, I am sorry.
        symbols = ['INSERT INTO',
                   'nightshades.unit_tags (unit_id, string)',
                   'VALUES',
                   ','.join(mogrify_me),
                   'RETURNING string']
        insert_sql = ' '.join(symbols) + ';'

        with self.conn.cursor() as curs:
            curs.execute(remove_sql, self.sql_opts)
            curs.execute(insert_sql, insert_opts)
            res = curs.fetchall()

        self.conn.commit()
        return (res, invalids,)


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
    def start_unit(self, seconds=1500):
        if self.is_unit_ongoing():
            return (False, 'This user already has an ongoing unit.',)

        sql = form_insert(
            insert    = 'nightshades.units (user_id, start_time, expiry_time)',
            values    = "%(user_id)s, NOW(), NOW() + INTERVAL '%(seconds)s seconds'",
            returning = 'id, expiry_time - NOW()',)

        opts = self.sql_opts.copy()
        opts['seconds'] = seconds

        with self.conn.cursor() as curs:
            curs.execute(sql, opts)
            row = curs.fetchone()
            self.conn.commit()

            return row
