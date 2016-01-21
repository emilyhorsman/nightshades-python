def form_select(*args, **kwargs):
    symbols = ['SELECT', kwargs['select'][0], 'FROM', kwargs['select'][1]]

    if 'where' in kwargs:
        symbols += ['WHERE', ' AND '.join(kwargs['where'])]

    if 'order' in kwargs:
        symbols += ['ORDER BY', kwargs['order']]

    return ' '.join(symbols) + ';'

class User:
    def __init__(self, conn, user_id):
        self.conn = conn
        self.user_id = user_id

    def get_units(self, show_incomplete=False):
        completion = []
        if not show_incomplete:
            completion.append("completed='t'")

        sql = form_select(
            select = ('id, completed, start_time, expiry_time', 'nightshades.units'),
            where  = ['user_id=%(user_id)s'] + completion,
            order  = 'expiry_time DESC',)

        opts = {
            'user_id': self.user_id
        }

        with self.conn.cursor() as curs:
            res = curs.execute(sql, opts)
            return curs.fetchall()
