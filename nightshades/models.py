from playhouse.postgres_ext import DateTimeTZField
from peewee import (
    Model, UUIDField, ForeignKeyField,
    TextField, BooleanField, SQL
)

from . import connection


class BaseModel(Model):
    class Meta:
        database = connection()


class User(BaseModel):
    id         = UUIDField(primary_key = True,
                           constraints = [SQL('DEFAULT uuid_generate_v4()')])
    name       = TextField()
    created_at = DateTimeTZField(constraints = [SQL("DEFAULT NOW()")])

    class Meta:
        db_table = 'users'


class LoginProvider(BaseModel):
    user             = ForeignKeyField(User, on_delete = 'CASCADE')
    provider         = TextField()
    provider_user_id = TextField()
    created_at       = DateTimeTZField(constraints = [SQL("DEFAULT NOW()")])

    class Meta:
        db_table = 'login_providers'

        indexes = (
            (('provider', 'provider_user_id'), True),
        )


class Unit(BaseModel):
    id          = UUIDField(primary_key = True,
                            constraints = [SQL('DEFAULT uuid_generate_v4()')])
    user        = ForeignKeyField(User, on_delete = 'CASCADE')
    completed   = BooleanField(default = False)
    description = TextField(null = True)
    start_time  = DateTimeTZField(constraints = [SQL("DEFAULT NOW()")])
    expiry_time = DateTimeTZField(constraints = [SQL("DEFAULT NOW() + INTERVAL '25 minutes'")])

    class Meta:
        db_table = 'units'


class Tag(BaseModel):
    unit   = ForeignKeyField(Unit, on_delete = 'CASCADE')
    string = TextField()

    class Meta:
        db_table = 'tags'

        indexes = (
            (('unit', 'string'), True),
        )
