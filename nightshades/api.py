import logging
import datetime

import peewee

from . import connection
from .models import User, Unit, Tag, LoginProvider, SQL

# This is how long one has after the expiry_time to mark a unit as complete.
expiry_interval = "INTERVAL '5 minutes'"


class UsageError(Exception):
    def __init__(self, message):
        Exception.__init__(self)
        self.message = message

    def __str__(self):
        return repr(self.message)


class ValidationError(UsageError):
    pass


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
    if seconds < 1200:
        raise ValidationError('Unit must be at least 2 minutes')

    if has_ongoing_unit(user_id):
        raise UsageError('User already has an going unit')

    return Unit.insert(
        user     = user_id,
        expiry_time = SQL("NOW() + INTERVAL '%s seconds'", seconds),
        description = description
    ).dicts().execute()


def mark_complete(unit_id):
    res = Unit.update(completed = True).where(
        Unit.id == unit_id,
        Unit.completed == False,
        Unit.expiry_time < SQL('NOW()'),
        SQL('NOW() <= expiry_time + {}'.format(expiry_interval))
    ).execute()

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

        valids.append({ 'unit_id': unit_id, 'string': tag })

    return (valids, invalids)


def set_tags(unit_id, tag_csv):
    db = connection()
    with db.transaction() as trans:
        Unit.delete().where(
            Unit.id == unit_id
        ).execute()

        if len(tag_csv.strip()) == 0:
            trans.commit()
            return []

        valids, invalids = validate_tag_csv(tag_csv)
        if len(valids) == 0:
            trans.rollback()
            raise ValidationError('No valid tags')

        with db.atomic():
            tags = Tag.insert_many(valids).execute().returning(Tag.string).tuples()

        trans.commit()

    return tags


def get_units(user_id, date_a, date_b):
    return Unit.select().join(Tag).where(
        Unit.user == user_id,
        SQL('start_time BETWEEN SYMMETRIC %s AND %s', date_a, date_b)
    ).order_by(Unit.start_time.desc()).dicts()


def query_ongoing_unit(user_id):
    unit = Unit.select().where(
        Unit.user == user_id,
        Unit.completed == False,
        Unit.expiry_time >= datetime.datetime.now()
    ).order_by(Unit.start_time.desc())

    return unit


def get_ongoing_unit(user_id):
    return query_ongoing_unit(user_id).dicts().get()


def has_ongoing_unit(user_id):
    return query_ongoing_unit(user_id).count()


# You can't cancel an ongoing unit that has exceeded its expiry_time, even if
# it is still within the grace period of the expiry threshold.
def cancel_ongoing_unit(user_id):
    unit = get_ongoing_unit(user_id, False)
    unit.delete_instance()


def register_user(name, provider, provider_user_id):
    if provider not in valid_login_providers:
        raise ValidationError('Not a valid login provider')

    # If we can't create the LoginProvider record as well, then we
    # shouldn't commit the User record.
    db = connection()
    try:
        with db.atomic():
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
        db.rollback()
        logging.error(e)
        raise ValidationError('Provider ID already used')


def login_via_provider(provider, provider_user_id):
    return User.select().join(LoginProvider).where(
        LoginProvider.provider == provider,
        LoginProvider.provider_user_id == provider_user_id
    ).dicts().get()
