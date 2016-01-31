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

os.environ['NIGHTSHADES_DOTENV'] = '.test.env'
from nightshades import load_dotenv
load_dotenv()

from nightshades import api
from nightshades.models import User, Unit, LoginProvider, Tag
from test_helpers import Test

class TestSession(unittest.TestCase):
    def test_connection_context(self):
        db = nightshades.connection()
        self.assertEqual(db.get_conn().status, psycopg2.extensions.STATUS_READY)


class TestUserModel(Test):
    def test_can_create_user(self):
        user = User.create(name = 'Alice')
        self.assertIsInstance(user.id, UUID)

        user = User.get(User.id == user.id)
        self.assertIsInstance(user.created_at, datetime.datetime)
        self.assertIsInstance(user.name, str)


class TestLoginProviderModel(Test):
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


class TestUnitModel(Test):
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


class TestTagModel(Test):
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


class TestGetUser(Test):
    def test_can_get_user(self):
        user = User.create(name = 'Alice')
        res = api.get_user(str(user.id))
        self.assertEqual(res['name'], 'Alice')


class TestMarkComplete(Test):
    def test_can_mark_complete(self):
        user = User.create(name = 'Alice')
        unit = Unit.create(
            user        = user,
            completed   = False,
            start_time  = SQL("NOW() - INTERVAL '00:25:00.1'"),
            expiry_time = SQL("NOW() - INTERVAL '00:00:00.1'")
        )

        res = api.mark_complete(unit.id)
        self.assertTrue(res)
        self.assertTrue(Unit.get(Unit.id == unit.id).completed)

    # Expired units have passed the grace period (their expiry_time plus the
    # expiry_interval)
    def test_cannot_mark_expired_unit_as_complete(self):
        user = User.create(name = 'Alice')
        unit = Unit.create(
            user        = user,
            start_time  = SQL("NOW() - INTERVAL '00:30:00'"),
            expiry_time = SQL("NOW() - {}".format(api.expiry_interval))
        )

        res = api.mark_complete(unit.id)
        self.assertFalse(res)
        self.assertFalse(Unit.get(Unit.id == unit.id).completed)

    # Ongoing units have not reached their expiry date yet.
    def test_cannot_mark_ongoing_unit_as_complete(self):
        user = User.create(name = 'Alice')
        unit = Unit.create(user = user)
        res = api.mark_complete(unit.id)
        self.assertFalse(res)
        self.assertFalse(Unit.get(Unit.id == unit.id).completed)

    def test_cannot_mark_completed_unit_as_complete(self):
        user = User.create(name = 'Alice')
        unit = Unit.create(user = user, completed = True)
        res = api.mark_complete(unit.id)
        self.assertFalse(res)
        self.assertTrue(Unit.get(Unit.id == unit.id).completed)


class TestOngoingUnit(Test):
    def test_ongoing_unit(self):
        user = User.create(name = 'Alice')
        unit = Unit.create(user = user)
        self.assertTrue(api.has_ongoing_unit(user.id))
        self.assertEqual(api.get_ongoing_unit(user.id)['id'], unit.id)

    def test_no_ongoing_unit(self):
        user = User.create(name = 'Alice')
        unit = Unit.create(user = user, completed = True)
        self.assertFalse(api.has_ongoing_unit(user.id))

        with self.assertRaises(api.NoOngoingUnit):
            api.get_ongoing_unit(user.id)


class TestStartUnit(Test):
    def test_fail_too_short(self):
        with self.assertRaisesRegex(api.ValidationError, 'at least'):
            user = User.create(name = 'Alice')
            api.start_unit(user.id, 119, 'foo')


    def test_cannot_start_unit_during_ongoing_unit(self):
        user = User.create(name = 'Alice')
        unit = Unit.create(
            user        = user,
            completed   = False,
            start_time  = SQL("NOW() - INTERVAL '25 minutes'"),
            expiry_time = SQL("NOW() + INTERVAL '1 second'"))

        with self.assertRaises(api.HasOngoingUnitAlready):
            api.start_unit(user.id)

    def test_start_unit(self):
        user    = User.create(name = 'Alice')
        unit_id = api.start_unit(user.id, 1200, 'Homework!')
        self.assertIsInstance(unit_id, UUID)


class TestValidateTagCSV(Test):
    def test_too_many_tags(self):
        with self.assertRaisesRegex(api.ValidationError, 'only have 5'):
            api.validate_tag_csv('foo', ',' * 5)

    def test_unique_tags_only(self):
        valids, invalids = api.validate_tag_csv('foo', 'bar,bar')
        self.assertEqual(len(valids), 1)
        self.assertEqual(len(invalids), 0)

    def test_separate_valids(self):
        tags = (
            'a' * 41,
            'bar',
            'baz ',
            '',
            '🤗' * 40,
        )
        valids, invalids = api.validate_tag_csv('foo', ','.join(tags))
        self.assertEqual(len(invalids), 1)
        self.assertEqual(invalids[0][0], 'a' * 41)
        self.assertEqual(len(valids), 3)
        self.assertIn({ 'unit': 'foo', 'string': '🤗' * 40 }, valids)
        self.assertIn({ 'unit': 'foo', 'string': 'baz' }, valids)
        self.assertNotIn({ 'unit': 'foo', 'string': '' }, valids)


class TestSetTags(Test):
    def test_set_tags(self):
        user = User.create(name = 'Alice')
        unit = Unit.create(user = user)
        tag  = Tag.create(unit = unit, string = 'this should be deleted')

        tags = api.set_tags(unit.id, 'bar,baz,foo,bal,bee')
        self.assertIn('foo', tags)
        self.assertEqual(len(tags), 5)

        res = list(Tag.select(Tag.string).where(Tag.unit == unit).tuples().execute())
        self.assertNotIn((tag.string,), res)
        self.assertEqual(len(res), 5)

    def test_no_valid_tags(self):
        user = User.create(name = 'Alice')
        unit = Unit.create(user = user)
        tag  = Tag.create(unit = unit, string = 'should not be deleted')
        with self.assertRaisesRegex(api.ValidationError, 'No valid tags'):
            api.set_tags(unit.id, 'a' * 41)

        self.assertTrue(Tag.select().where(Tag.unit == unit).count())

    def test_delete_on_blank_string(self):
        user = User.create(name = 'Alice')
        unit = Unit.create(user = user)
        tag  = Tag.create(unit = unit, string = 'should be deleted')
        res  = api.set_tags(unit.id, '')
        self.assertEqual(res, [])
        self.assertFalse(Tag.select().where(Tag.unit == unit).count())


class TestGetUnits(Test):
    def test_get_units(self):
        user = User.create(name = 'Alice')

        # This unit starts just before the 3rd and should not be included
        Unit.create(
            user        = user,
            completed   = True,
            start_time  = SQL("TIMESTAMP WITH TIME ZONE '2016-01-02 23:59:59.999999-5'"),
            expiry_time = SQL("TIMESTAMP WITH TIME ZONE '2016-01-03 00:00:01.000000-5'"))

        # This unit starts just after the 9th and should not be included
        Unit.create(
            user        = user,
            completed   = False,
            start_time  = SQL("TIMESTAMP WITH TIME ZONE '2016-01-10 00:00:00.000000-5'"),
            expiry_time = SQL("TIMESTAMP WITH TIME ZONE '2016-01-10 00:00:01.000000-5'"))

        # This unit starts on the 3rd and should be included
        unit_yesa = Unit.create(
            user        = user,
            completed   = True,
            start_time  = SQL("TIMESTAMP WITH TIME ZONE '2016-01-03 00:00:00.000000-5'"),
            expiry_time = SQL("TIMESTAMP WITH TIME ZONE '2016-01-03 00:00:01.000000-5'"))

        # This unit starts on the 9th and should be included
        unit_yesb = Unit.create(
            user        = user,
            completed   = True,
            start_time  = SQL("TIMESTAMP WITH TIME ZONE '2016-01-09 23:59:59.999999-5'"),
            expiry_time = SQL("TIMESTAMP WITH TIME ZONE '2016-01-10 00:00:01.000000-5'"))

        # Get all units between (inclusive) the 3rd and 9th
        tz = datetime.timezone(datetime.timedelta(hours = -5))
        units = api.get_units(
            user.id,
            datetime.datetime(2016, 1, 3, tzinfo = tz),
            datetime.datetime(2016, 1, 9, 23, 59, 59, 999999, tzinfo = tz))

        self.assertEqual(len(units), 2)
        ids = list(map(lambda u: u.get('id'), units))
        self.assertIn(unit_yesa.id, ids)
        self.assertIn(unit_yesb.id, ids)


class TestCancelOngoingUnit(Test):
    def test_cancel_ongoing_unit(self):
        user = User.create(name = 'Alice')
        unit = Unit.create(user = user)
        self.assertTrue(api.cancel_ongoing_unit(user))

        with self.assertRaises(peewee.DoesNotExist):
            Unit.get(Unit.id == unit.id)


class TestLoginProvider(Test):
    def test_invalid_login_provider(self):
        with self.assertRaises(api.InvalidLoginProvider):
            api.register_user('Alice', 'foobar', uuid4())

    def test_can_register_user_and_login(self):
        puid = uuid4()
        user_id = api.register_user('Alice', 'twitter', puid)
        self.assertIsInstance(user_id, UUID)

        logged_in_user = api.login_via_provider('twitter', puid)
        self.assertEqual(user_id, logged_in_user.get('id'))

    def test_cannot_use_provider_twice(self):
        puid = uuid4()
        name = str(uuid4())
        api.register_user('Alice', 'twitter', puid)
        with self.assertRaisesRegex(api.ValidationError, 'Provider ID already used'):
            api.register_user(name, 'twitter', puid)

        with self.assertRaises(peewee.DoesNotExist):
            User.get(User.name == name).id

from http_tests import *

if __name__ == '__main__':
    logging.basicConfig(filename = 'nightshades_tests.log')
    unittest.main()
