import os
from playhouse.db_url import connect

def connection():
    k = 'NIGHTSHADES_POSTGRESQL_DB_URI'
    db_conn_uri = os.environ.get(k, default = 'postgresqlext:///nightshades')
    return connect(db_conn_uri, register_hstore = False)


def load_dotenv():
    import dotenv

    # I really don't like libraries that assume the dotenv file is in the
    # current working directory, so give the option.
    custom_location = os.environ.get('NIGHTSHADES_DOTENV')
    if custom_location:
        path = os.path.expanduser(custom_location)
    else:  # pragma: no cover
        path = os.path.join(os.getcwd(), '.env')

    dotenv.load_dotenv(path)
