import os
import contextlib

import psycopg2

def connection():
    k = 'NIGHTSHADES_POSTGRESQL_DB_STR'
    db_conn_str = os.environ.get(k, default = 'dbname=nightshades')
    return psycopg2.connect(db_conn_str)

def load_dotenv():
    import dotenv

    # I really don't like libraries that assume the dotenv file is in the
    # current working directory, so give the option.
    custom_location = os.environ.get('NIGHTSHADES_DOTENV')
    if custom_location:
        path = os.path.expanduser(custom_location)
    else: # pragma: no cover
        path = os.path.join(os.getcwd(), '.env')

    dotenv.load_dotenv(path)
