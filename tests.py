import os
import unittest

import nightshades
from psycopg2.extensions import STATUS_READY

def load_dotenv():
    os.environ['NIGHTSHADES_DOTENV'] = '.test.env'
    nightshades.load_dotenv()

class TestSession(unittest.TestCase):
    def setUp(self):
        load_dotenv()

    def test_connection_context(self):
        with nightshades.connection() as conn:
            self.assertEqual(conn.status, STATUS_READY)

class TestUnits(unittest.TestCase):
    def create_dummy_user(self, conn, curs):
        curs.execute("INSERT INTO nightshades.users (name) VALUES ('Alice') RETURNING id")
        conn.commit()
        self.user_id = curs.fetchone()[0]

    def setUp(self):
        load_dotenv()

        with nightshades.connection() as conn:
            with conn.cursor() as curs:
                self.create_dummy_user(conn, curs)

    def test_user_created(self):
        self.assertIsNotNone(self.user_id)


if __name__ == '__main__':
    unittest.main()
