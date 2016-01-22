# -*- coding: utf-8 -*-

import os
import datetime
import unittest

import nightshades

# Decorator to pass the connection into the test function.
def with_connection(func):
    def with_context_manager(self):
        with nightshades.connection() as conn:
            func(self, conn)

    return with_context_manager

# Decorator to pass the connection and a new cursor into the test function.
def with_connection_and_cursor(func):
    def with_context_managers(self):
        with nightshades.connection() as conn:
            with conn.cursor() as curs:
                func(self, conn, curs)

    return with_context_managers

def create_user(curs):
    curs.execute("INSERT INTO nightshades.users (name) VALUES ('Alice') RETURNING id")
    return curs.fetchone()[0]

def create_unit(curs, **kwargs):
    keys    = '(user_id, completed, start_time, expiry_time)'
    values  = '(%s, %s, {}, {})'.format(kwargs['start_time'], kwargs['expiry_time'])
    sql     = 'INSERT INTO nightshades.units {} VALUES {}'.format(keys, values)
    sql    += ' RETURNING id;'
    curs.execute(sql, (kwargs['user_id'], kwargs['completed'],))

    return curs.fetchone()[0]

def create_user_with_unit(conn, **kwargs):
    with conn.cursor() as curs:
        kwargs['user_id'] = create_user(curs)
        unit_id = create_unit(curs, **kwargs)
        conn.commit()
        return (kwargs['user_id'], unit_id)

# Test #connection
class TestSession(unittest.TestCase):
    def test_connection_context(self):
        import psycopg2
        with nightshades.connection() as conn:
            self.assertEqual(conn.status, psycopg2.extensions.STATUS_READY)


# Test Unit#time_left
class TestUnitTimeLeft(unittest.TestCase):
    # Should get a negative time delta for completed units.
    # Should get a correct, positive time delta for ongoing units.
    @with_connection
    def test_unit_time_left(self, conn):
        with conn.cursor() as curs:
            user_id = create_user(curs)
            keys = '(user_id, completed, start_time, expiry_time)'
            values_list = (
                "(%(user_id)s, TRUE, TIMESTAMP 'TODAY', TIMESTAMP 'TODAY' + INTERVAL '25 minutes')",
                "(%(user_id)s, FALSE, NOW(), NOW() + INTERVAL '25 minutes')",)

            def get_id(values):
                sql = "INSERT INTO nightshades.units {} VALUES {} RETURNING id;".format(keys, values)
                curs.execute(sql, { 'user_id': user_id })
                return curs.fetchone()[0]

            ids = tuple(map(get_id, values_list))
            curs.execute("SELECT TIMESTAMP 'TODAY' + INTERVAL '25 minutes' - NOW();")
            conn.commit()
            delta = curs.fetchone()[0]

        complete_delta = nightshades.api.Unit(conn, user_id, ids[0]).time_left()
        self.assertTrue(complete_delta.total_seconds() < 0)

        # assertEqual(complete_delta.total_seconds(), delta.total_seconds())
        # may fail because of microsecond differences, thus assume reasonable
        # bound:
        expected = complete_delta.total_seconds() - delta.total_seconds()
        self.assertTrue(expected < 0)
        self.assertTrue(expected > -1)

        # 0:24:59 < delta <= 0:25:00
        incomplete_delta = nightshades.api.Unit(conn, user_id, ids[1]).time_left()
        self.assertTrue(incomplete_delta > datetime.timedelta(seconds=1499))
        self.assertTrue(incomplete_delta <= datetime.timedelta(seconds=1500))

        conn.rollback()

# Test Unit#mark_complete
class TestUnitMarkComplete(unittest.TestCase):
    # Should be able to mark an incomplete but expired unit as complete.
    @with_connection
    def test_can_mark_unit_complete(self, conn):
        user_id, unit_id = create_user_with_unit(conn,
                completed   = False,
                start_time  = "NOW() - INTERVAL '00:25:00.1'",
                expiry_time = "NOW() - INTERVAL '00:00:00.1'")

        unit = nightshades.api.Unit(conn, user_id, unit_id)
        self.assertTrue(unit.mark_complete())

        with conn.cursor() as curs:
            curs.execute("SELECT completed FROM nightshades.units WHERE id=%s;", (unit_id,))
            self.assertTrue(curs.fetchone()[0],
                    msg='Unit should be marked as complete.')

    # Should not be able to mark a unit as complete if it has passed the
    # expiry threshold.
    @with_connection
    def test_cannot_mark_expired_unit_as_complete(self, conn):
        user_id, unit_id = create_user_with_unit(conn,
                completed   = False,
                start_time  = "NOW() - INTERVAL '00:30:00'",
                expiry_time = "NOW() - {}".format(nightshades.api.expiry_interval))

        unit = nightshades.api.Unit(conn, user_id, unit_id)
        res = unit.mark_complete()
        self.assertFalse(res[0])

    # Should not be able to mark an ongoing unit that has not expired as complete.
    @with_connection
    def test_cannot_mark_ongoing_unit_as_complete(self, conn):
        user_id, unit_id = create_user_with_unit(conn,
                completed   = False,
                start_time  = "NOW()",
                expiry_time = "NOW() + INTERVAL '1 minute'")

        unit = nightshades.api.Unit(conn, user_id, unit_id)
        res = unit.mark_complete()
        self.assertFalse(res[0])

        with conn.cursor() as curs:
            curs.execute("SELECT completed FROM nightshades.units WHERE id=%s;", (unit_id,))
            self.assertFalse(curs.fetchone()[0],
                    msg='Unit should not have been marked completed in the database.')

    # Should return an error if we try to mark a completed unit as complete.
    @with_connection
    def test_cannot_mark_completed_unit_as_complete(self, conn):
        user_id, unit_id = create_user_with_unit(conn,
                completed   = True,
                start_time  = "NOW() - INTERVAL '2 minutes'",
                expiry_time = "NOW() - INTERVAL '1 minute'")

        unit = nightshades.api.Unit(conn, user_id, unit_id)
        res = unit.mark_complete()
        self.assertFalse(res[0])

# Test Unit#update_tags
class TestUnitUpdateTags(unittest.TestCase):
    # Should add and overwrite past tags.
    @with_connection
    def test_add_and_overwrite_tags(self, conn):
        user_id, unit_id = create_user_with_unit(conn,
                completed   = False,
                start_time  = "NOW()",
                expiry_time = "NOW() + INTERVAL '25 minutes'")

        unit = nightshades.api.Unit(conn, user_id, unit_id)
        tags_res = unit.update_tags("😍, bar, baz, omg,hi")

        with conn.cursor() as curs:
            curs.execute('SELECT string FROM nightshades.unit_tags WHERE unit_id=%s',
                    (unit_id,))
            check_res = curs.fetchall()

            self.assertEqual(sorted(check_res), sorted(tags_res[0]))

            # Sanity check
            self.assertIn(('hi',), check_res)
            self.assertIn(('omg',), check_res)

        tags_res = unit.update_tags("a,b,c ")
        with conn.cursor() as curs:
            curs.execute('SELECT string FROM nightshades.unit_tags WHERE unit_id=%s',
                    (unit_id,))
            check_res = curs.fetchall()

            self.assertEqual(sorted(check_res), sorted(tags_res[0]))

            # Sanity check
            self.assertIn(('c',), check_res)
            self.assertNotIn(('hi,'), check_res)

    # Should not accept more than 5 tags
    @with_connection
    def test_no_more_than_five_tags(self, conn):
        user_id, unit_id = create_user_with_unit(conn,
                completed   = False,
                start_time  = "NOW()",
                expiry_time = "NOW() + INTERVAL '25 minutes'")

        unit = nightshades.api.Unit(conn, user_id, unit_id)
        res  = unit.update_tags("a,b,c,d,e,f")
        self.assertFalse(res[0])

    # Should spit tags over 40 characters back as invalid.
    # Should not insert blank tags.
    @with_connection
    def test_tag_validation(self, conn):
        user_id, unit_id = create_user_with_unit(conn,
                completed   = False,
                start_time  = "NOW()",
                expiry_time = "NOW() + INTERVAL '25 minutes'")

        unit = nightshades.api.Unit(conn, user_id, unit_id)
        res  = unit.update_tags(",," + "a" * 41 + "," + "💆" * 40 + ",bar")
        self.assertEqual(len(res[0]), 2,
                msg='Only the two valid tags should have been inserted.')
        self.assertIn(('bar',), res[0])
        self.assertIn(('💆'*40,), res[0])
        self.assertEqual(len(res[1]), 1)

    # Should not insert duplicates.
    @with_connection
    def test_tag_duplicates(self, conn):
        user_id, unit_id = create_user_with_unit(conn,
                completed   = False,
                start_time  = "NOW()",
                expiry_time = "NOW() + INTERVAL '25 minutes'")

        unit = nightshades.api.Unit(conn, user_id, unit_id)
        res  = unit.update_tags("bar,bar,foo")
        self.assertEqual(len(res[0]), 2)


# Test User#is_unit_ongoing
class TestUserIsUnitOngoing(unittest.TestCase):
    # Should return True if there is an ongoing, incomplete unit.
    @with_connection
    def test_returns_true(self, conn):
        user_id, _ = create_user_with_unit(conn,
                completed   = False,
                start_time  = "NOW()",
                expiry_time = "NOW() + INTERVAL '1 minute'")

        user = nightshades.api.User(conn, user_id)
        self.assertTrue(user.is_unit_ongoing())

    # Should return False if the user has no units.
    @with_connection
    def test_returns_false_if_no_units(self, conn):
        with conn.cursor() as curs:
            user_id = create_user(curs)

        user = nightshades.api.User(conn, user_id)
        self.assertFalse(user.is_unit_ongoing())

    # Should return False if the user has no ongoing units. This includes units
    # that were not completed but passed the expiry threshold.
    @with_connection
    def test_returns_false_if_no_ongoing_unit(self, conn):
        # This unit is expired and was completed.
        user_id, unit_id = create_user_with_unit(conn,
                completed   = True,
                start_time  = "NOW() - INTERVAL '00:30:00.1'",
                expiry_time = "NOW() - {} - INTERVAL '00:00:00.1'".format(nightshades.api.expiry_interval))

        with conn.cursor() as curs:
            # This unit is expired and was not completed.
            create_unit(curs,
                    user_id     = user_id,
                    completed   = False,
                    start_time  = "NOW() - INTERVAL '00:30:00.1'",
                    expiry_time = "NOW() - {} - INTERVAL '00:00:00.1'".format(nightshades.api.expiry_interval))
            conn.commit()

        user = nightshades.api.User(conn, user_id)
        self.assertFalse(user.is_unit_ongoing())

# Test User#cancel_ongoing_unit
class TestUserCancelOngoingUnit(unittest.TestCase):
    # Should be able to cancel an ongoing unit that has not expired.
    @with_connection
    def test_cancel_ongoing_unit(self, conn):
        user_id, unit_id = create_user_with_unit(conn,
                completed   = False,
                start_time  = "NOW() - INTERVAL '00:00:00.1'",
                expiry_time = "NOW() + INTERVAL '1 minute'")

        user = nightshades.api.User(conn, user_id)
        res  = user.cancel_ongoing_unit()
        self.assertTrue(res[0], msg=res)

        with conn.cursor() as curs:
            curs.execute('SELECT COUNT(id) FROM nightshades.units WHERE id=%s', (unit_id,))
            self.assertEqual(curs.fetchone()[0], 0)

    # Should not be able to cancel an incomplete unit that expired.
    @with_connection
    def test_dont_cancel_expired_unit(self, conn):
        user_id, unit_id = create_user_with_unit(conn,
                completed   = False,
                start_time  = "NOW() - INTERVAL '00:30:00'",
                expiry_time = "NOW() - {} - INTERVAL '00:00:00.1'".format(nightshades.api.expiry_interval))

        user = nightshades.api.User(conn, user_id)
        res  = user.cancel_ongoing_unit()
        self.assertFalse(res[0], msg=res)
        self.assertEqual(res[2], 0)

        with conn.cursor() as curs:
            curs.execute('SELECT COUNT(id) FROM nightshades.units WHERE id=%s', (unit_id,))
            self.assertEqual(curs.fetchone()[0], 1,
                    msg='Expired unit was not supposed to be deleted.')


# Test User#start_unit
class TestUserStartUnit(unittest.TestCase):
    # Should be able to start a new unit and receive back a uuid and delta.
    @with_connection_and_cursor
    def test_start_unit(self, conn, curs):
        user_id = create_user(curs)
        user    = nightshades.api.User(conn, user_id)
        res     = user.start_unit(minutes=20)

        self.assertEqual(res[0].count('-'), 4,
                msg='First unit tuple item does not look like a UUID.')

        self.assertEqual(res[1].total_seconds(), 1200,
                msg='Did not receive expected delta, {}'.format(res))

    # Should not start a new unit if there is one ongoing.
    @with_connection_and_cursor
    def test_dont_start_new_unit(self, conn, curs):
        user_id = create_user(curs)
        user    = nightshades.api.User(conn, user_id)

        _, res = user.start_unit(), user.start_unit()
        self.assertFalse(res[0],
                msg='Should not have started second ongoing unit.')

from http_tests import *

if __name__ == '__main__':
    os.environ['NIGHTSHADES_DOTENV'] = '.test.env'
    nightshades.load_dotenv()
    unittest.main()
