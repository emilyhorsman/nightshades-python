import nightshades
from flask import g


def conn():
    conn = g.get('conn', None)
    if conn is None:
        conn = g.conn = nightshades.connection()

    return conn
