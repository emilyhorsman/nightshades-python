from . import connection
from playhouse.postgres_ext import DateTimeTZField
from peewee import (
    Model, UUIDField, ForeignKeyField,
    TextField, BooleanField, SQL
)


class BaseModel(Model):
    class Meta:
        database = connection()

class User(BaseModel):
    id         = UUIDField(primary_key = True)
    name       = TextField()
    created_at = DateTimeTZField(default = SQL("NOW()"))

    class Meta:
        db_table = 'users'

class LoginProvider(BaseModel):
    user_id          = ForeignKeyField(User)
    provider         = TextField()
    provider_user_id = TextField()

    class Meta:
        db_table = 'login_providers'

        indexes = (
            (('provider', 'provider_user_id'), True),
        )

class Unit(BaseModel):
    id          = UUIDField(primary_key = True)
    user_id     = ForeignKeyField(User)
    completed   = BooleanField(default = False)
    description = TextField(null = True)
    start_time  = DateTimeTZField(default = SQL("NOW()"))
    expiry_time = DateTimeTZField(default = SQL("NOW() + INTERVAL '25 minutes'"))

    class Meta:
        db_table = 'units'

class Tag(BaseModel):
    unit_id = ForeignKeyField(Unit)
    string  = TextField()

    class Meta:
        db_table = 'tags'

        indexes = (
            (('unit_id', 'string'), True),
        )
