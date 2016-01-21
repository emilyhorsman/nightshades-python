def form_select(*args, **kwargs):
    symbols = ['SELECT', kwargs['select'][0], 'FROM', kwargs['select'][1]]

    if 'where' in kwargs:
        symbols += ['WHERE', ' AND '.join(kwargs['where'])]

    if 'order' in kwargs:
        symbols += ['ORDER BY', kwargs['order']]

    return ' '.join(symbols) + ';'

def form_insert(*args, **kwargs):
    symbols  = ['INSERT INTO', kwargs['insert']]
    symbols += ['VALUES (', kwargs['values'], ')']

    if 'returning' in kwargs:
        symbols += ['RETURNING', kwargs['returning']]

    return ' '.join(symbols) + ';'

def form_delete(*args, **kwargs):
    symbols = ['DELETE FROM', kwargs['delete']]

    if 'where' in kwargs:
        symbols += ['WHERE', ' AND '.join(kwargs['where'])]

    return ' '.join(symbols) + ';'

def form_update(*args, **kwargs):
    symbols = ['UPDATE', kwargs['update'][0], 'SET', kwargs['update'][1]]

    if 'where' in kwargs:
        symbols += ['WHERE', ' AND '.join(kwargs['where'])]

    return ' '.join(symbols) + ';'
