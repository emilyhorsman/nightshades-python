import os
import datetime
import unittest

import nightshades
from psycopg2.extensions import STATUS_READY

class TestSession(unittest.TestCase):
    def test_connection_context(self):
        with nightshades.connection() as conn:
            self.assertEqual(conn.status, STATUS_READY)

# Decorator to pass the connection into the test function.
def with_connection(func):
    def with_context_manager(self):
        with nightshades.connection() as conn:
            func(self, conn)

    return with_context_manager

class TestUnits(unittest.TestCase):
    @with_connection
    def setUp(self, conn):
        with conn.cursor() as curs:
            curs.execute("INSERT INTO nightshades.users (name) VALUES ('Alice') RETURNING id")
            conn.commit()
            self.user_id = curs.fetchone()[0]

    @with_connection
    def tearDown(self, conn):
        with conn.cursor() as curs:
            curs.execute("DELETE FROM nightshades.units WHERE user_id=%s", (self.user_id,))
            curs.execute("DELETE FROM nightshades.users WHERE id=%s", (self.user_id,))
            conn.commit()

    @with_connection
    def test_user_created_and_has_no_units(self, conn):
        self.assertIsNotNone(self.user_id)
        user = nightshades.api.User(conn, self.user_id)
        num_units = len(user.get_units(show_incomplete=True))
        self.assertEqual(num_units, 0)

    @with_connection
    def test_start_new_unit_flow(self, conn):
        user = nightshades.api.User(conn, self.user_id)

        res = user.start_unit(minutes=20)
        self.assertNotEqual(res[0], False)
        self.assertEqual(res[1].seconds, 1200)

        res = user.start_unit()
        self.assertFalse(res[0],
                msg='Should not create a unit while ongoing.')

        units = user.get_units()
        self.assertEqual(len(units), 0,
                msg='Should not show incomplete units by default.')

        units = user.get_units(show_incomplete=True)
        self.assertEqual(len(units), 1,
                msg='Should have one incomplete unit available.')

        self.assertEqual(units[0][0].count('-'), 4,
                msg='Unit Index 0 should be UUID')
        self.assertFalse(units[0][1],
                msg='Unit Index 1 should be incomplete boolean')
        self.assertIsInstance(units[0][2], datetime.datetime)
        self.assertIsInstance(units[0][3], datetime.datetime)
        self.assertTrue(units[0][2] < units[0][3])

        unit = nightshades.api.Unit(conn, self.user_id, units[0][0])
        time_left = unit.time_left()
        self.assertTrue(time_left > datetime.timedelta(seconds=1199))
        self.assertTrue(time_left < datetime.timedelta(seconds=1200))

        res = unit.mark_complete()
        self.assertFalse(res[0],
                msg='Unit not past expiry should be able to be marked complete.')

        conn.rollback()


if __name__ == '__main__':
    os.environ['NIGHTSHADES_DOTENV'] = '.test.env'
    nightshades.load_dotenv()
    unittest.main()
