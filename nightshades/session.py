import os
import dotenv
from playhouse.postgres_ext import PostgresqlExtDatabase
from playhouse.db_url import parse


def connection():
    k = 'NIGHTSHADES_POSTGRESQL_DB_URI'
    db_conn_uri = os.environ.get(k, default = 'postgresqlext:///nightshades')

    opts = parse(db_conn_uri)
    opts.update(dict(
        register_hstore = False,
        autorollback = True
    ))

    return PostgresqlExtDatabase(**opts)


def load_dotenv():
    # I really don't like libraries that assume the dotenv file is in the
    # current working directory, so give the option.
    custom_location = os.environ.get('NIGHTSHADES_DOTENV')
    if custom_location:
        path = os.path.expanduser(custom_location)
    else:  # pragma: no cover
        path = os.path.join(os.getcwd(), '.env')

    dotenv.load_dotenv(path)
