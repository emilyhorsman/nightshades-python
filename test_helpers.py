import nightshades


# Decorator to pass the connection into the test function.
def with_connection(func):
    def with_context_manager(self):
        with nightshades.connection() as conn:
            func(self, conn)

    return with_context_manager


# Decorator to pass the connection and a new cursor into the test function.
def with_connection_and_cursor(func):
    def with_context_managers(self):
        with nightshades.connection() as conn:
            with conn.cursor() as curs:
                func(self, conn, curs)

    return with_context_managers


def create_user(curs):
    curs.execute("INSERT INTO nightshades.users (name) VALUES ('Alice') RETURNING id")
    return curs.fetchone()[0]


def create_unit(curs, **kwargs):
    keys    = '(user_id, completed, start_time, expiry_time)'
    values  = '(%s, %s, {}, {})'.format(kwargs['start_time'], kwargs['expiry_time'])
    sql     = 'INSERT INTO nightshades.units {} VALUES {}'.format(keys, values)
    sql    += ' RETURNING id;'
    curs.execute(sql, (kwargs['user_id'], kwargs['completed'],))

    return curs.fetchone()[0]


def create_user_with_unit(conn, **kwargs):
    with conn.cursor() as curs:
        kwargs['user_id'] = create_user(curs)
        unit_id = create_unit(curs, **kwargs)
        conn.commit()
        return (kwargs['user_id'], unit_id)
