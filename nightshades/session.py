import os
import contextlib

import psycopg2

class connection(contextlib.ContextDecorator):
    def __enter__(self):
        self.db_conn_str = os.environ.get('NIGHTSHADES_POSTGRESQL_DB_STR',
                                default = 'dbname=nightshades')

        self.connection = psycopg2.connect(self.db_conn_str)
        return self.connection

    def __exit__(self, *exc):
        self.connection.close()

def load_dotenv():
    import dotenv

    # I really don't like libraries that assume the dotenv file is in the
    # current working directory, so give the option.
    custom_location = os.environ.get('NIGHTSHADES_DOTENV')
    if custom_location:
        path = os.path.expanduser(custom_location)

    path = os.path.join(os.getcwd(), '.env')

    dotenv.load_dotenv(path)
