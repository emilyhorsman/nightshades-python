# -*- coding: utf-8 -*-
import logging
import datetime

import peewee

from .models import db, User, Unit, Tag, LoginProvider, SQL

# This is how long one has after the expiry_time to mark a unit as complete.
expiry_interval = "INTERVAL '5 minutes'"


class UsageError(Exception):
    '''An exception thrown when the API has been used improperly, typically a
    parent class.
    '''
    def __init__(self, message = ''):
        Exception.__init__(self)
        self.message = message

    def __str__(self):
        return repr(self.message)


class ValidationError(UsageError): pass
class HasOngoingUnitAlready(UsageError): pass
class NoOngoingUnit(UsageError): pass
class InvalidLoginProvider(UsageError): pass


# Let's define some things.
#
# Unit states:
#   * completed: Unit.completed == true
#   * ongoing: NOW() < Unit.expiry_time
#   * expired: NOW() > Unit.expiry_time + expiry_threshold

valid_login_providers = (
    'twitter',
    'facebook',
)


def start_unit(user_id, seconds = 1500, description = None):
    '''Start a unit for a given user with a default period of 25 minutes.

    :param user_id: a unique identifier for the user
    :type user_id: `str` or `UUID`
    :param int seconds: number of seconds in the new unit
    :param str description: human-friendly description for the user of the unit
    :return: UUID of new unit (the primary key) if created
    :rtype: `UUID`
    :raises ValidationError: if the specified unit is less than 2 minutes
    :raises HasOngoingUnitAlready: if the user already has an ongoing unit
    '''

    if seconds < 120:
        raise ValidationError('Unit must be at least 2 minutes')

    if has_ongoing_unit(user_id):
        raise HasOngoingUnitAlready

    return Unit.insert(
        user        = user_id,
        expiry_time = SQL("NOW() + INTERVAL '%s seconds'", seconds),
        description = description
    ).dicts().execute()


def mark_complete(unit_id, **kwargs):
    '''Mark a given unit as completed. This must be done within the expiry
    threshold of the unit’s expiry_time.

    :param unit_id: the ID of the unit
    :type unit_id: `str` or `UUID`
    :return: True if a unit was updated
    :rtype: bool
    '''

    filters = [
        Unit.id == unit_id,
        Unit.completed == False,
        Unit.expiry_time < SQL('NOW()'),
        SQL('NOW() <= expiry_time + {}'.format(expiry_interval)),
    ]

    if kwargs.get('user_id', False):
        filters.append(Unit.user == kwargs['user_id'])

    res = Unit.update(completed = True).where(*filters).execute()
    return res == 1


def validate_tag_csv(unit_id, tag_csv):
    if tag_csv.count(',') >= 5:
        raise ValidationError('Unit can only have 5 tags')

    invalids = []
    valids   = []
    for _tag in set(tag_csv.split(',')):  # Unique tags only
        tag = _tag.strip()
        if not tag:
            continue

        if len(tag) > 40:
            invalids.append((tag, 'Over 40 characters'))
            continue

        valids.append({ 'unit': unit_id, 'string': tag })

    return (valids, invalids)


def set_tags(unit_id, tag_csv):
    '''Replace the tags of a unit with a given string of comma-separated tags.

    :raises ValidationError: if more than 5 tags are given
    '''
    valids, invalids = validate_tag_csv(unit_id, tag_csv)

    # If a blank string is received then all tags should be deleted even if
    # not replaced by other tags. If a non-blank string is received but there
    # are no valid tags, raise a ValidationError.
    if len(tag_csv) > 0 and len(valids) == 0:
        raise ValidationError('No valid tags')

    with db.atomic() as trans:
        Tag.delete().where(
            Tag.unit_id == unit_id
        ).execute()

        if len(valids) > 0:
            tags = Tag.insert_many(valids).returning(Tag.string).tuples().execute()
            trans.commit()
            return list(map(lambda t: t[0], tags))

    return []


def get_unit(unit_id, **kwargs):
    filters = [Unit.id == unit_id]
    if kwargs.get('user_id', False):
        filters.append(Unit.user == kwargs['user_id'])

    return Unit.select().where(*filters).dicts().get()


def get_units(user_id, date_a, date_b):
    return Unit.select().where(
        Unit.user == user_id,
        SQL('start_time BETWEEN SYMMETRIC %s AND %s', date_a, date_b),
    ).order_by(Unit.start_time.desc()).dicts()


def query_ongoing_unit(user_id):
    unit = Unit.select().where(
        Unit.user == user_id,
        Unit.completed == False,
        Unit.expiry_time >= datetime.datetime.now()
    ).order_by(Unit.start_time.desc())

    return unit


def get_ongoing_unit(user_id):
    try:
        return query_ongoing_unit(user_id).dicts().get()
    except peewee.DoesNotExist as e:
        logging.error(e)
        raise NoOngoingUnit


def has_ongoing_unit(user_id):
    return query_ongoing_unit(user_id).count()


# You can't cancel an ongoing unit that has exceeded its expiry_time, even if
# it is still within the grace period of the expiry threshold.
def cancel_ongoing_unit(user_id):
    unit = query_ongoing_unit(user_id)
    return unit.get().delete_instance()


def register_user(name, provider, provider_user_id):
    if provider not in valid_login_providers:
        raise InvalidLoginProvider

    # If we can't create the LoginProvider record as well, then we
    # shouldn't commit the User record.
    try:
        with db.atomic() as trans:
            user = User.insert(
                name = name
            ).tuples().execute()

            LoginProvider.create(
                user             = user,
                provider         = provider,
                provider_user_id = provider_user_id
            )

        return user
    except peewee.IntegrityError as e:
        trans.rollback()
        logging.error(e)
        raise ValidationError('Provider ID already used')


def login_via_provider(provider, provider_user_id):
    return User.select().join(LoginProvider).where(
        LoginProvider.provider == provider,
        LoginProvider.provider_user_id == provider_user_id
    ).dicts().get()


def add_new_provider(user_id, provider, provider_user_id):
    return LoginProvider.create(
        user          = user_id,
        provider         = provider,
        provider_user_id = provider_user_id
    )
