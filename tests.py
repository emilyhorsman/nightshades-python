# -*- coding: utf-8 -*-

import os
import datetime
import random
import unittest
import logging
from uuid import UUID, uuid4

import psycopg2
import peewee
from peewee import SQL

import nightshades
from nightshades.models import User, Unit, LoginProvider, Tag

class TestSession(unittest.TestCase):
    def test_connection_context(self):
        db = nightshades.connection()
        self.assertEqual(db.get_conn().status, psycopg2.extensions.STATUS_READY)


class TestUserModel(unittest.TestCase):
    def test_can_create_user(self):
        user = User.create(name = 'Alice')
        self.assertIsInstance(user.id, UUID)

        user = User.get(User.id == user.id)
        self.assertIsInstance(user.created_at, datetime.datetime)
        self.assertIsInstance(user.name, str)


class TestLoginProviderModel(unittest.TestCase):
    def test_can_create_login_provider_model(self):
        login = LoginProvider.create(
            user = User.create(name = 'Alice'),
            provider         = 'twitter',
            provider_user_id = uuid4()
        )

        login = LoginProvider.get(LoginProvider.id == login.id)
        self.assertEqual(login.provider, 'twitter')
        self.assertIsInstance(login.created_at, datetime.datetime)

    def test_unique_provider(self):
        uid = uuid4()
        login = LoginProvider.create(
            user = User.create(name = 'Alice'),
            provider         = 'twitter',
            provider_user_id = uid
        )

        with self.assertRaisesRegex(peewee.IntegrityError, 'duplicate key'):
            login = LoginProvider.create(
                user = User.create(name = 'Alice'),
                provider         = 'twitter',
                provider_user_id = uid
            )


        login = LoginProvider.create(
            user = User.create(name = 'Alice'),
            provider = 'facebook',
            provider_user_id = uid
        )
        self.assertIsNotNone(login.id)

    def test_providers_deleted_on_user_delete(self):
        user = User.create(name = 'Alice')
        login = LoginProvider.create(
            user = user,
            provider = 'twitter',
            provider_user_id = uuid4()
        )

        user.delete_instance()
        with self.assertRaises(peewee.DoesNotExist):
            LoginProvider.get(LoginProvider.id == login.id)


class TestUnitModel(unittest.TestCase):
    def test_can_create_unit_model(self):
        user = User.create(name = 'Alice')
        unit = Unit.create(user = user, description = 'foo')
        unit = Unit.get(Unit.id == unit.id)

        self.assertEqual(unit.description, 'foo')
        self.assertFalse(unit.completed)
        self.assertIsInstance(unit.id, UUID)
        self.assertIsInstance(unit.start_time, datetime.datetime)
        self.assertIsInstance(unit.expiry_time, datetime.datetime)

    def test_units_deleted_on_user_delete(self):
        user = User.create(name = 'Alice')
        unit = Unit.create(user = user)

        user.delete_instance()
        with self.assertRaises(peewee.DoesNotExist):
            Unit.get(Unit.id == unit.id)


class TestTagModel(unittest.TestCase):
    def test_can_create_tag_model(self):
        user = User.create(name = 'Alice')
        unit = Unit.create(user = user)
        tag = Tag.create(unit = unit, string = 'foobar')
        tag = Tag.get(Tag.id == tag.id)
        self.assertEqual(tag.string, 'foobar')

    def test_tags_deleted_on_unit_delete(self):
        user = User.create(name = 'Alice')
        unit = Unit.create(user = user)
        tag = Tag.create(unit = unit, string = 'foobar')
        unit.delete_instance()
        with self.assertRaises(peewee.DoesNotExist):
            Tag.get(Tag.id == tag.id)

    def test_tags_are_unique(self):
        user = User.create(name = 'Alice')
        unit = Unit.create(user = user)
        Tag.create(unit = unit, string = 'foobar')
        with self.assertRaisesRegex(peewee.IntegrityError, 'duplicate key'):
            Tag.create(unit = unit, string = 'foobar')


class TestMarkComplete(unittest.TestCase):
    def test_can_mark_complete(self):
        user = User.create(name = 'Alice')
        unit = Unit.create(
            user        = user,
            completed   = False,
            start_time  = SQL("NOW() - INTERVAL '00:25:00.1'"),
            expiry_time = SQL("NOW() - INTERVAL '00:00:00.1'")
        )

        res = nightshades.api.mark_complete(unit.id)
        self.assertTrue(res)
        self.assertTrue(Unit.get(Unit.id == unit.id).completed)

    # Expired units have passed the grace period (their expiry_time plus the
    # expiry_interval)
    def test_cannot_mark_expired_unit_as_complete(self):
        user = User.create(name = 'Alice')
        unit = Unit.create(
            user        = user,
            start_time  = SQL("NOW() - INTERVAL '00:30:00'"),
            expiry_time = SQL("NOW() - {}".format(nightshades.api.expiry_interval))
        )

        res = nightshades.api.mark_complete(unit.id)
        self.assertFalse(res)
        self.assertFalse(Unit.get(Unit.id == unit.id).completed)

    # Ongoing units have not reached their expiry date yet.
    def test_cannot_mark_ongoing_unit_as_complete(self):
        user = User.create(name = 'Alice')
        unit = Unit.create(user = user)
        res = nightshades.api.mark_complete(unit.id)
        self.assertFalse(res)
        self.assertFalse(Unit.get(Unit.id == unit.id).completed)

    def test_cannot_mark_completed_unit_as_complete(self):
        user = User.create(name = 'Alice')
        unit = Unit.create(user = user, completed = True)
        res = nightshades.api.mark_complete(unit.id)
        self.assertFalse(res)
        self.assertTrue(Unit.get(Unit.id == unit.id).completed)


if __name__ == '__main__':
    logging.basicConfig(filename = 'nightshades_tests.log')
    os.environ['NIGHTSHADES_DOTENV'] = '.test.env'
    nightshades.load_dotenv()
    unittest.main()
