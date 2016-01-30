import unittest

from nightshades.models import db


class Test(unittest.TestCase):
    def setUp(self):
        db.connect()

    def tearDown(self):
        db.connect()
